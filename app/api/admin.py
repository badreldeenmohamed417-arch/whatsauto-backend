from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.api.auth import get_current_user

router = APIRouter()

class UserAdminResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    role: str
    plan: str
    
class PlanUpdateRequest(BaseModel):
    user_id: int
    plan: str

# Admin Middleware equivalent
def get_current_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

@router.get("/users", response_model=List[UserAdminResponse])
def get_all_users(admin_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.post("/upgrade_plan")
def upgrade_user_plan(req: PlanUpdateRequest, admin_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.plan = req.plan
    db.commit()
    return {"message": "Plan updated successfully", "user_id": user.id, "new_plan": user.plan}
