import json
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    GuidelineDocument,
    GuidelineChunk,
)

RULES_DIR = (
    Path(__file__).resolve().parent.parent
    / "rules"
)

async def seed_guidelines_if_empty(
    db: AsyncSession,
):
    existing = await db.scalar(
        select(GuidelineDocument.id)
    )
    if existing:
        return
    for file_path in RULES_DIR.glob("*.json"):
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        document = GuidelineDocument(
            authority=data["authority"],
            document_name=data.get(
                "document_name",
                file_path.stem,
            ),
            authority_rank=data.get(
                "authority_rank",
                99,
            ),
            source_file=data.get(
                "source_file",
                file_path.name,
            ),
        )

        db.add(document)
        for key, value in data.items():

            if key in {
                "document_name",
                "version",
                "source_file",
                "extraction_date",
                "authority",
                "authority_rank",
                "rank_context",
                "rank_note",
                "authority_scope",
                "note",
            }:
                continue
            chunk = GuidelineChunk(
                authority=data["authority"],
                section_key=key,
                section_name=key.replace(
                    "_",
                    " "
                ).title(),
                source_page=(
                    str(value.get("source_page"))
                    if isinstance(value, dict)
                    and value.get("source_page")
                    else None
                ),
                authority_scope=data.get(
                    "authority_scope"
                ),
                content=value,
            )

            db.add(chunk)
    await db.commit()