from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base

class Tweet(Base):
    __tablename__ = "tweets"

    tweet_timestamp: Mapped[str] = mapped_column(String, primary_key=True)
    tweet_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    tweet_link: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc)
    )