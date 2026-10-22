"""Account-owned collection; revisions are only inserted, never edited by APIs."""
from sqlalchemy import ForeignKey, String, JSON, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column


def collection_models(Base, Owned):
    class DailyCheckin(Owned, Base):
        __tablename__ = 'daily_checkins'
        __table_args__ = (UniqueConstraint('owner_id', 'date', name='daily_owner_date'),
            CheckConstraint('revision >= 1', name='daily_revision_positive'))
        id: Mapped[int] = mapped_column(primary_key=True)
        owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
        date: Mapped[str] = mapped_column(String(10))
        timezone_name: Mapped[str] = mapped_column(String(100))
        created_at: Mapped[str] = mapped_column(String(40))
        revision: Mapped[int] = mapped_column(default=1)
        deleted_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
        values: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    class CheckinRevision(Owned, Base):
        __tablename__ = 'checkin_revisions'
        __table_args__ = (UniqueConstraint('checkin_id', 'revision', name='checkin_revision_unique'),)
        id: Mapped[int] = mapped_column(primary_key=True)
        owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)
        checkin_id: Mapped[int] = mapped_column(ForeignKey('daily_checkins.id'))
        revision: Mapped[int] = mapped_column()
        action: Mapped[str] = mapped_column(String(20))
        recorded_at: Mapped[str] = mapped_column(String(40))
        values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    return DailyCheckin, CheckinRevision
