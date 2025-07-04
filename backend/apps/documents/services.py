from . import models
from backend.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

class DraftService:
    @staticmethod
    async def create_draft(db: AsyncSession, template_id: uuid.UUID, user_id: uuid.UUID):
        draft = models.Draft(template_id=template_id, user_id=user_id)
        db.add(draft)
        await db.commit()
        await db.refresh(draft)
        return draft

    @staticmethod
    async def save_version(db: AsyncSession, draft_id: uuid.UUID, content: dict):
        version = models.Version(draft_id=draft_id, content=content)
        db.add(version)
        await db.commit()
        return version

    @staticmethod
    async def finalize_draft(db: AsyncSession, draft_id: uuid.UUID, content: dict):
        draft = await db.get(models.Draft, draft_id)
        draft.status = "finalized"
        document = models.Document(draft_id=draft_id, final_content=content)
        db.add(document)
        await db.commit()
        return document