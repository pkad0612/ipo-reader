import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/meta/ipo.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS files(
            file_id TEXT PRIMARY KEY,
            filename TEXT,
            pages INTEGER,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def upsert_file(file_id: str, filename: str, status: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO files(file_id, filename, status)
        VALUES(?,?,?)
        ON CONFLICT(file_id) DO UPDATE SET
            filename=excluded.filename,
            status=excluded.status,
            updated_at=CURRENT_TIMESTAMP
        """, (file_id, filename, status))
        conn.commit()

def set_status(file_id: str, status: str):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE files SET status=?, updated_at=CURRENT_TIMESTAMP WHERE file_id=?", (status, file_id))
        conn.commit()

def get_status(file_id: str) -> Optional[str]:
    with get_conn() as conn:
        c = conn.cursor()
        r = c.execute("SELECT status FROM files WHERE file_id=?", (file_id,)).fetchone()
        return r["status"] if r else None
def list_files(status: str = "done", limit: int = 50):
    with get_conn() as conn:
        c = conn.cursor()
        rows = c.execute(
            "SELECT file_id, filename, status, created_at, updated_at FROM files WHERE status=? ORDER BY updated_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
        return [dict(r) for r in rows]
