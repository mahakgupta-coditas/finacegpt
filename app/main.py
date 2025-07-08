from fastapi import FastAPI
from app.routers.upload import router as upload_document
from app.routers.query import router as query_router
from app.routers.session import router as session_router
from app.routers.comparison import router as comparison_router
from app.routers.querylog import router as querylog_router

app = FastAPI(title="FinanceGPT API")

# Include routers
app.include_router(upload_document)
app.include_router(query_router)
app.include_router(session_router)
app.include_router(comparison_router)
app.include_router(querylog_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to FinanceGPT API"}
