#!/usr/bin/env python3
"""
Database initialization script
"""
import asyncio
from sqlalchemy import create_engine
from app.config import settings
from app.db import Base
from app.models import User
from app.auth import get_password_hash

def init_database():
    """Initialize the database with tables and seed data"""
    # Create engine
    engine = create_engine(settings.database_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Create admin user if it doesn't exist
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created (username: admin, password: admin)")
        else:
            print("ℹ️  Admin user already exists")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
