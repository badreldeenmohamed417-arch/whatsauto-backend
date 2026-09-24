from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.db.session import get_db
from app.models.user import User, ChannelConfig
from app.api.settings import get_current_user

router = APIRouter()

class ChannelConfigResponse(BaseModel):
    id: int
    platform: str
    channel_id: str
    is_active: bool

class ChannelConfigCreate(BaseModel):
    platform: str
    channel_id: str
    token: str = ""

@router.get("/", response_model=List[ChannelConfigResponse])
def get_channels(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(ChannelConfig).filter(ChannelConfig.user_id == current_user.id).all()

@router.post("/", response_model=ChannelConfigResponse)
def connect_channel(data: ChannelConfigCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    channel = db.query(ChannelConfig).filter(
        ChannelConfig.user_id == current_user.id,
        ChannelConfig.platform == data.platform
    ).first()
    
    if channel:
        channel.channel_id = data.channel_id
        channel.is_active = True
    else:
        channel = ChannelConfig(
            user_id=current_user.id,
            platform=data.platform,
            channel_id=data.channel_id,
            is_active=True
        )
        db.add(channel)
    
    db.commit()
    db.refresh(channel)
    return channel
