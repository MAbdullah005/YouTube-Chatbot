from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.schemas import SignupRequest, SignupResponse
from backend.auth.security import hash_password
from backend.db.deps import get_db
from datetime import datetime
from backend.models.users import User

from backend.models.email_verification import EmailVerification
from backend.auth.token_utils import generate_token, hash_token
from backend.auth.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=SignupResponse)
async def signup(data: SignupRequest, db: Session = Depends(get_db)):
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

    token = generate_token()
    token_hash = hash_token(token)

    verification = EmailVerification(
      user_id=user.id,
      token_hash=token_hash,
      expires_at=EmailVerification.expiry_time()
  )

    db.add(verification)
    db.commit()

    await send_verification_email(user.email, token)

    # 4️⃣ Save to DB
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Signup successful. Please verify your email."}





@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    token_hash = hash_token(token)

    record = db.query(EmailVerification).filter(
        EmailVerification.token_hash == token_hash
    ).first()

    if not record:
        raise HTTPException(status_code=400, detail="Invalid token")

    if record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.is_verified = True

    db.delete(record)
    db.commit()

    return {"message": "Email verified successfully"}

