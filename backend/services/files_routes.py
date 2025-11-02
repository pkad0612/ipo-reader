from fastapi import APIRouter, Query
from store.db import get_conn

router = APIRouter()

@router.get("/files")
def list_files(status: str = Query("done"), limit: int = Query(50)):
    """List all processed files with status."""
    with get_conn() as conn:
        c = conn.cursor()
        rows = c.execute(
            "SELECT file_id, filename, status, updated_at FROM files WHERE status=? ORDER BY updated_at DESC LIMIT ?",
            (status, limit)
        ).fetchall()
        return {"files": [dict(r) for r in rows]}
