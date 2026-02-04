from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timedelta
from backend.db.base import Base

class PasswordReset(Base):
    __tablename__ = "password_reset"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    @staticmethod
    def expiry_time():
        return datetime.utcnow() + timedelta(minutes=15)
