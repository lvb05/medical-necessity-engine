from datetime import datetime, timezone
from sqlalchemy import (
    Text,
    DateTime,
    String,
    JSON,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)
class Base(DeclarativeBase):
    pass

class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    question: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    authority_used: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    source_section: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    billed_code: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    denial_risk: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class GuidelineDocument(Base):
    __tablename__ = "guideline_documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    authority: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )
    document_name: Mapped[str] = mapped_column(
        String(255),
    )

    authority_rank: Mapped[int] = mapped_column()
    source_file: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

class GuidelineChunk(Base):
    __tablename__ = "guideline_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    authority: Mapped[str] = mapped_column(
        String(50),
    )
    section_key: Mapped[str] = mapped_column(
        String(255),
    )
    section_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source_page: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    authority_scope: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    content: Mapped[dict] = mapped_column(
        JSON,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )