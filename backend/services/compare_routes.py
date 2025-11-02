from fastapi import APIRouter
from pydantic import BaseModel
from services.compare import compare_ipos

router = APIRouter()

class CompareReq(BaseModel):
    file_id_1: str
    file_id_2: str

@router.post("/compare")
def compare_endpoint(payload: CompareReq):
    return compare_ipos(payload.file_id_1, payload.file_id_2)
