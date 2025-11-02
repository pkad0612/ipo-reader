from pydantic import BaseModel
from typing import Optional


class UploadInitResp(BaseModel):
    file_id: str


class UploadCompleteReq(BaseModel):
    file_id: str
    filename: str
    total_chunks: int


class JobStatusResp(BaseModel):
    job_id: str
    status: str
    message: Optional[str] = None
