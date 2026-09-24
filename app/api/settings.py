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
    from datetime import datetime, timezone
    return bool(user.expires_at and user.expires_at > datetime.now(timezone.utc) and user.subscription_status == "ACTIVE")

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
    from datetime import datetime, timezone
    active = subscription_active(current_user)
    return {
        "status": "ACTIVE" if active else "EXPIRED",
        "expires_at": current_user.expires_at.isoformat() if current_user.expires_at else None,
        "days_remaining": max(0, (current_user.expires_at - datetime.now(timezone.utc)).days) if current_user.expires_at else 0
    }
