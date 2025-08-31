from sqlalchemy import Column, DateTime, Integer, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
