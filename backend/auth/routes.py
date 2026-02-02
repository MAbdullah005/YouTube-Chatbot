from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.schemas import SignupRequest, SignupResponse
from backend.auth.security import hash_password
from backend.db.deps import get_db
from backend.models.users import User

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=SignupResponse)
def signup(data: SignupRequest, db: Session = Depends(get_db)):
    # 1️⃣ Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2️⃣ Hash password
    hashed_password = hash_password(data.password)

    # 3️⃣ Create user
    user = User(
        email=data.email,
        password_hash=hashed_password,
        is_verified=False
    )

    # 4️⃣ Save to DB
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Signup successful. Please verify your email."}
