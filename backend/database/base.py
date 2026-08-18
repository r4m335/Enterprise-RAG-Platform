from typing import Any
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    id: Any
    __name__: str

    # Generate __tablename__ automatically
    @classmethod
    def __declare_last__(cls):
        if not hasattr(cls, "__tablename__"):
            cls.__tablename__ = cls.__name__.lower()
