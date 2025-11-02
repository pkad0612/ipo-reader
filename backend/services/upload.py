import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from models.schemas import UploadInitResp, UploadCompleteReq, JobStatusResp
from store.db import upsert_file, set_status, get_status
from services.pipeline import process_pipeline

TMP_DIR = Path("data/tmp")
RAW_DIR = Path("data/raw")
TMP_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

@router.post("/upload/init", response_model=UploadInitResp)
def upload_init(filename: str):
    file_id = str(uuid.uuid4())
    upsert_file(file_id, filename, status="init")
    return UploadInitResp(file_id=file_id)

@router.post("/upload/chunk")
def upload_chunk(
    file: UploadFile = File(...),
    x_file_id: str = Header(..., convert_underscores=False),
    x_chunk_index: int = Header(..., convert_underscores=False),
    x_total_chunks: int = Header(..., convert_underscores=False),
):
    # basic validations
    if not x_file_id:
        raise HTTPException(status_code=400, detail="Missing X-File-Id")
    if x_chunk_index < 0 or x_total_chunks < 1:
        raise HTTPException(status_code=400, detail="Invalid chunk headers")

    part_dir = TMP_DIR / x_file_id
    part_dir.mkdir(parents=True, exist_ok=True)

    part_path = part_dir / f"{x_chunk_index}.part"
    with open(part_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    set_status(x_file_id, "uploaded")
    return {"ok": True, "received_chunk": x_chunk_index, "total_chunks": x_total_chunks}

@router.post("/upload/complete")
def upload_complete(payload: UploadCompleteReq, background: BackgroundTasks):
    part_dir = TMP_DIR / payload.file_id
    if not part_dir.exists():
        raise HTTPException(status_code=400, detail="No chunks found for file_id")

    dest = RAW_DIR / f"{payload.file_id}.pdf"
    # assemble parts in order (0..total_chunks-1)
    with open(dest, "wb") as fout:
        for i in range(payload.total_chunks):
            part_path = part_dir / f"{i}.part"
            if not part_path.exists():
                raise HTTPException(status_code=400, detail=f"Missing chunk {i}")
            with open(part_path, "rb") as fin:
                shutil.copyfileobj(fin, fout)

    upsert_file(payload.file_id, payload.filename, status="assembled")
    # kick background processing
    background.add_task(process_pipeline, payload.file_id)
    return {"job_id": payload.file_id, "message": "Processing started"}

@router.get("/status/{job_id}", response_model=JobStatusResp)
def status(job_id: str):
    status = get_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return JobStatusResp(job_id=job_id, status=status, message=None)
