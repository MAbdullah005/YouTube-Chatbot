from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.schemas import SignupRequest, SignupResponse
from backend.auth.security import hash_password
from backend.db.deps import get_db
from datetime import datetime


from backend.auth.security import verify_password
from backend.auth.jwt_utils import create_access_token
from backend.auth.schemas import LoginRequest, LoginResponse
from backend.models.users import User
from backend.auth.email import send_reset_email 
from backend.auth.email import get_current_user

from backend.models.password_reset import PasswordReset
from backend.models.email_verification import EmailVerification
from backend.auth.token_utils import generate_token, hash_token
from backend.auth.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=SignupResponse)
async def signup(data: SignupRequest, db: Session = Depends(get_db)):

    # 1️⃣ Check existing user
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2️⃣ Hash password
    hashed_password = hash_password(data.password)

    # 3️⃣ Create & SAVE user FIRST
    user = User(
        email=data.email,
        password_hash=hashed_password,
        is_verified=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)   # ✅ NOW user.id EXISTS

    # 4️⃣ Create verification token
    token = generate_token()
    token_hash = hash_token(token)

    verification = EmailVerification(
        user_id=user.id,   # ✅ VALID ID
        token_hash=token_hash,
        expires_at=EmailVerification.expiry_time()
    )

    db.add(verification)
    db.commit()

    # 5️⃣ Send email
    await send_verification_email(user.email, token)

    return {"message": "Signup successful. Please verify your email."}


@router.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_verified": current_user.is_verified
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    token_hash = hash_token(token)

    record = (
        db.query(EmailVerification)
        .filter(EmailVerification.token_hash == token_hash)
        .first()
    )

    if not record:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    if record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user = db.query(User).filter(User.id == record.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True

    # delete token after use
    db.delete(record)
    db.commit()

    return {"message": "Email verified successfully"}





@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):

    # 1️⃣ Find user
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 2️⃣ Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 3️⃣ BLOCK unverified users 🔥🔥🔥
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )

    # 4️⃣ Create JWT
    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()

    # Always return same message (security)
    if not user:
        return {"message": "If the email exists, a reset link was sent"}

    token = generate_token()
    token_hash = hash_token(token)

    reset = PasswordReset(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=PasswordReset.expiry_time()
    )

    db.add(reset)
    db.commit()

    await send_reset_email(user.email, token)

    return {"message": "If the email exists, a reset link was sent"}



@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    token_hash = hash_token(token)

    record = (
        db.query(PasswordReset)
        .filter(PasswordReset.token_hash == token_hash)
        .first()
    )

    if not record:
        raise HTTPException(status_code=400, detail="Invalid token")

    if record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(new_password)

    db.delete(record)
    db.commit()

    return {"message": "Password reset successful"}
