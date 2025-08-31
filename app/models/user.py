from sqlalchemy import Boolean, Column, String

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # TODO: should be extended with more fields for user profile

    def __repr__(self):
        return f"<User(email={self.email})>"
