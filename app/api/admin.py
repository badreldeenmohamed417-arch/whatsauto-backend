from datetime import datetime, timezone
import calendar
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.api.settings import get_current_user

router = APIRouter()

class UserAdminResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    role: str
    subscription_status: str
    expires_at: datetime | None = None

class SubscriptionRequest(BaseModel):
    user_id: int
    months: int = 1

def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

def add_months(dt: datetime, months: int) -> datetime:
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)

@router.get("/users", response_model=list[UserAdminResponse])
def get_all_users(
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id.desc()).all()

@router.post("/subscriptions/activate")
def activate_subscription(
    req: SubscriptionRequest,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if req.months < 1 or req.months > 24:
        raise HTTPException(status_code=400, detail="months must be between 1 and 24")

    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now(timezone.utc)
    expires = user.expires_at
    if expires is None:
        expires = now
    elif expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        expires = now

    user.expires_at = add_months(expires, req.months)
    user.subscription_status = "ACTIVE"
    db.commit()
    db.refresh(user)

    return {
        "message": "Subscription activated",
        "user_id": user.id,
        "status": user.subscription_status,
        "expires_at": user.expires_at,
    }

@router.post("/subscriptions/disable")
def disable_subscription(
    req: SubscriptionRequest,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.subscription_status = "EXPIRED"
    user.expires_at = None
    db.commit()
    return {"message": "Subscription disabled", "user_id": user.id}
