from fastapi import Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.auth import get_current_active_user
from app.models import User


def get_current_user_dependency() -> User:
    return Depends(get_current_active_user)


def get_db_dependency() -> Session:
    return Depends(get_db)
