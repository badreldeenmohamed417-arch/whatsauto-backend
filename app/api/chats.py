from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User, Conversation
from app.api.settings import get_current_user

router = APIRouter()

@router.get("")
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [{
        "id": c.id,
        "channel": c.channel_type,
        "customer_id": c.customer_id,
        "customer_name": c.customer_name,
        "updated_at": c.updated_at,
        "messages": [{"sender": m.sender, "content": m.content, "created_at": m.created_at} for m in c.messages]
    } for c in conversations]

@router.get("/{conversation_id}")
def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conversation.id,
        "channel": conversation.channel_type,
        "customer_id": conversation.customer_id,
        "customer_name": conversation.customer_name,
        "messages": [{"sender": m.sender, "content": m.content, "created_at": m.created_at} for m in conversation.messages]
    }
