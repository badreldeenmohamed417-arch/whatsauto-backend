from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.db.session import get_db
from app.models.user import User, BotConfig
from app.core.security import ALGORITHM, SECRET_KEY

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    return user

def subscription_active(user: User) -> bool:
    if not user.expires_at or user.subscription_status != "ACTIVE":
        return False
    expires = user.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    return expires > datetime.now(timezone.utc)

class BotConfigUpdate(BaseModel):
    company_name: str = ""
    description: str = ""
    products: str = ""
    instructions: str = ""
    tone: str = "professional"
    handover_number: str = ""
    is_active: bool = True

class BotConfigResponse(BotConfigUpdate):
    id: int

@router.get("/bot", response_model=BotConfigResponse)
def get_bot_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user.id).first()
    if not config:
        config = BotConfig(user_id=current_user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("/bot", response_model=BotConfigResponse)
def update_bot_config(data: BotConfigUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user.id).first()
    if not config:
        config = BotConfig(user_id=current_user.id)
        db.add(config)
    config.company_name = data.company_name.strip()
    config.description = data.description.strip()
    config.products = data.products.strip()
    config.instructions = data.instructions.strip()
    config.tone = data.tone
    config.handover_number = data.handover_number.strip()
    config.is_active = data.is_active
    db.commit()
    db.refresh(config)
    return config

@router.get("/subscription")
def get_subscription(current_user: User = Depends(get_current_user)):
    expires = current_user.expires_at
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    active = subscription_active(current_user)
    days = max(0, (expires - datetime.now(timezone.utc)).days) if expires else 0
    return {
        "status": "ACTIVE" if active else "EXPIRED",
        "expires_at": expires.isoformat() if expires else None,
        "days_remaining": days
    }
