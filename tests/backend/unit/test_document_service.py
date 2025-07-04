import pytest
from backend.apps.documents import services
from backend.apps.documents.models import Draft
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_draft(db_session: AsyncSession):
    draft = await services.DraftService.create_draft(
        db_session, 
        template_id=uuid.uuid4(),
        user_id=uuid.uuid4()
    )
    assert draft.id is not None
    assert draft.status == "draft"

@pytest.mark.asyncio
async def test_save_version(db_session: AsyncSession):
    draft = await services.DraftService.create_draft(...)
    version = await services.DraftService.save_version(
        db_session,
        draft_id=draft.id,
        content={"key": "value"}
    )
    assert version.id is not None
    assert version.content == {"key": "value"}