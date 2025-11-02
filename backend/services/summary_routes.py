from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.summary import generate_summaries

router = APIRouter()

class SummaryReq(BaseModel):
    file_id: str

@router.post("/summary")
def summary_endpoint(payload: SummaryReq):
    try:
        result = generate_summaries(payload.file_id)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
