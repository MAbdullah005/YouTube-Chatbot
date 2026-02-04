from fastapi import FastAPI
from backend.auth.routes import router as auth_router
from backend.models.email_verification import EmailVerification
from backend.db.base import Base
from backend.db.session import engine

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
