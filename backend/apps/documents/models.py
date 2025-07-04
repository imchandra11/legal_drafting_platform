from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from backend.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    
    @classmethod
    async def get(cls, db: AsyncSession, user_id: uuid.UUID):
        stmt = select(cls).where(cls.id == user_id)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str):
        stmt = select(cls).where(cls.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()
    
    @classmethod
    async def create(cls, db: AsyncSession, user_data: dict):
        user = cls(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @classmethod
    async def update(cls, db: AsyncSession, user_id: uuid.UUID, update_data: dict):
        stmt = (
            update(cls)
            .where(cls.id == user_id)
            .values(update_data)
            .returning(cls)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalars().first()
    
    @classmethod
    async def get_or_create_oauth_user(
        cls, 
        db: AsyncSession, 
        email: str, 
        oauth_provider: str, 
        oauth_id: str,
        full_name: str = None
    ):
        user = await cls.get_by_email(db, email)
        if user:
            # Update last login and OAuth info
            await cls.update(db, user.id, {
                "last_login": func.now(),
                "oauth_provider": oauth_provider,
                "oauth_id": oauth_id
            })
            return user
        
        # Create new OAuth user
        user = cls(
            email=email,
            full_name=full_name,
            oauth_provider=oauth_provider,
            oauth_id=oauth_id,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update_last_login(self, db: AsyncSession):
        self.last_login = datetime.utcnow()
        await db.commit()
        await db.refresh(self)