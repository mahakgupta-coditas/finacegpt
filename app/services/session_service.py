import uuid
from sqlalchemy.orm import Session
from app.models.chatsession import ChatSession

def create_chat_session(db: Session):
    session_id = str(uuid.uuid4())
    session = ChatSession(session_id=session_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.session_id}
