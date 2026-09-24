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
    channels = db.query(ChannelConfig).filter(ChannelConfig.user_id == current_user.id).all()
    return [
        {
            "id": c.id,
            "platform": c.channel_type,
            "channel_id": c.provider_id or "",
            "is_active": c.is_active
        } for c in channels
    ]

@router.post("/", response_model=ChannelConfigResponse)
def connect_channel(data: ChannelConfigCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    channel = db.query(ChannelConfig).filter(
        ChannelConfig.user_id == current_user.id,
        ChannelConfig.channel_type == data.platform
    ).first()
    
    if channel:
        channel.provider_id = data.channel_id
        channel.is_active = True
    else:
        channel = ChannelConfig(
            user_id=current_user.id,
            channel_type=data.platform,
            provider_id=data.channel_id,
            is_active=True
        )
        db.add(channel)
    
    db.commit()
    db.refresh(channel)
    return {
        "id": channel.id,
        "platform": channel.channel_type,
        "channel_id": channel.provider_id,
        "is_active": channel.is_active
    }
