from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Player(Base):
    __tablename__ = 'players'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    position: Mapped[str] = mapped_column(String(120), default='')
    club: Mapped[str] = mapped_column(String(255), default='')
    nationality: Mapped[str] = mapped_column(String(120), default='')
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_value: Mapped[str] = mapped_column(String(120), default='')
    source: Mapped[str] = mapped_column(String(120), default='Pep.AI')
    raw_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reports: Mapped[list['ScoutingReport']] = relationship(back_populates='player')
    tactical_profiles: Mapped[list['TacticalProfile']] = relationship(back_populates='player')


class ScoutingReport(Base):
    __tablename__ = 'scouting_reports'
    __table_args__ = (UniqueConstraint('cache_key', name='uq_scouting_reports_cache_key'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), index=True)
    requested_system: Mapped[str] = mapped_column(String(255), index=True)
    buying_club: Mapped[str] = mapped_column(String(255), default='')
    cache_key: Mapped[str] = mapped_column(String(255), index=True)
    fit_score: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    consistency_score: Mapped[int] = mapped_column(Integer, default=0)
    development_notes: Mapped[str] = mapped_column(Text, default='')
    report_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    player: Mapped[Player] = relationship(back_populates='reports')


class TacticalProfile(Base):
    __tablename__ = 'tactical_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), index=True)
    system: Mapped[str] = mapped_column(String(255), index=True)
    identified_system: Mapped[str] = mapped_column(String(255), default='')
    role: Mapped[str] = mapped_column(String(255), default='')
    fit_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    player: Mapped[Player] = relationship(back_populates='tactical_profiles')


class Comparison(Base):
    __tablename__ = 'comparisons'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), index=True)
    compared_player_external_id: Mapped[str] = mapped_column(String(120), index=True)
    compared_player_name: Mapped[str] = mapped_column(String(255), default='')
    similarity_score: Mapped[int] = mapped_column(Integer, default=0)
    tactical_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_delta: Mapped[int] = mapped_column(Integer, default=0)
    matrix: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class KnowledgeSource(Base):
    __tablename__ = 'knowledge_sources'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(255), default='')
    content_hash: Mapped[str] = mapped_column(String(128), default='')
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlayerSearchHistory(Base):
    __tablename__ = 'player_search_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(255), index=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
