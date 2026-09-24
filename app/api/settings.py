from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from app.db.session import get_db
from app.models.user import User, BotConfig, ChannelConfig
from app.schemas.user import UserResponse
from app.core.security import ALGORITHM, SECRET_KEY
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

class BotConfigUpdate(BaseModel):
    company_name: str = ""
    system_prompt: str = ""
    tone: str = "professional"
    is_active: bool = True

class BotConfigResponse(BotConfigUpdate):
    id: int

@router.get("/bot", response_model=BotConfigResponse)
def get_bot_config(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user.id).first()
    if not config:
        config = BotConfig(user_id=current_user.id, system_prompt="", is_active=True)
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
    
    config.company_name = data.company_name
    config.system_prompt = data.system_prompt
    config.tone = data.tone
    config.is_active = data.is_active
    
    db.commit()
    db.refresh(config)
    return config
