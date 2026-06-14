from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import (
    AskRequest,
    AskResponse,
)
from app.database import get_db
from app.models import QueryLog

from app.engines.ask_engine import answer_question

router = APIRouter(
    prefix="/api",
    tags=["Ask"],
)

@router.post(
    "/ask",
    response_model=AskResponse,
)
async def ask_question(
    payload: AskRequest,
    db: AsyncSession = Depends(get_db),
):

    result = await answer_question(
        payload.question,
        db,
    )
    db.add(
        QueryLog(
            endpoint="/api/ask",
            question=payload.question,
            authority_used=result["authority"],
            source_section=result["source_section"],
            answer=result["answer"],
        )
    )
    try:
        await db.commit()
    except Exception:
        await db.rollback()
    return AskResponse(**result)