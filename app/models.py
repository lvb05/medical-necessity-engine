from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import Text
from sqlalchemy import DateTime
from sqlalchemy import String

from datetime import datetime


class Base(DeclarativeBase):
    pass


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    question: Mapped[str] = mapped_column(Text)

    authority_used: Mapped[str] = mapped_column(String(50))

    answer: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )