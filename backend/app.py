from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.upload import router as upload_router
from store.db import init_db
from services.qa_routes import router as qa_router
from services.risk_routes import router as risk_router
from services.summary_routes import router as summary_router
from services.compare_routes import router as compare_router
from services.files_routes import router as files_router





app = FastAPI(title="IPO Reader Backend")

# CORS: allow your local Next.js later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

# Routes
app.include_router(upload_router, prefix="")
app.include_router(qa_router, prefix="")
app.include_router(risk_router, prefix="")
app.include_router(summary_router, prefix="")
app.include_router(compare_router, prefix="")
app.include_router(files_router, prefix="")




