from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.qa import answer_question

router = APIRouter()

class QARequest(BaseModel):
    file_id: str
    query: str

@router.post("/qa")
def qa_endpoint(payload: QARequest):
    try:
        response = answer_question(payload.file_id, payload.query)
        return response
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
