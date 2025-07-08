from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db_utils.database import get_db
from app.services.session_service import create_chat_session

router = APIRouter(prefix="/session", tags=["Session"])

@router.post("/create")
def create_session_endpoint(db: Session = Depends(get_db)):
    return create_chat_session(db)
