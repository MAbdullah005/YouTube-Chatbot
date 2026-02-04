from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from backend.db.deps import get_db
from backend.models.users import User

# This should match your secret key & algorithm in jwt_utils
from backend.auth.jwt_utils import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


conf = ConnectionConfig(
    MAIL_USERNAME="abdullahaliofc@gmail.com",
    MAIL_PASSWORD="qdniczxeckijfqyb",
    MAIL_FROM="abdullahaliofc@gmail.com",
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,

    MAIL_STARTTLS=True,   # ✅ NEW
    MAIL_SSL_TLS=False,  # ✅ NEW

    USE_CREDENTIALS=True
)

async def send_verification_email(email: str, token: str):
    link = f"http://127.0.0.1:8000/auth/verify-email?token={token}"

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=f"Click the link to verify your email:\n\n{link}",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_reset_email(email: str, token: str):
    """
    Sends a password reset email to the user
    """
    reset_link = f"http://127.0.0.1:8000/auth/reset-password?token={token}"

    message = MessageSchema(
        subject="Reset Your Password",
        recipients=[email],
        body=f"Hi,\n\nClick the link below to reset your password:\n\n{reset_link}\n\n"
             f"This link will expire in 15 minutes.\n\n"
             f"If you didn't request a password reset, ignore this email.",
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)





def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get the currently logged-in user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user
