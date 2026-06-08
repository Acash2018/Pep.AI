from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Player
from app.db.session import SessionLocal
from app.services.football_metadata import enrich_player_metadata

PUBLIC_DATA_SOURCE = 'StatsBomb Open Data'
UPLOAD_DATA_SOURCE = 'S3 Upload'
INGESTED_DATA_SOURCES = {PUBLIC_DATA_SOURCE, UPLOAD_DATA_SOURCE}


def get_ingested_players(db: Session | None = None) -> list[dict[str, Any]]:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        players = db.scalars(select(Player).where(Player.source.in_(INGESTED_DATA_SOURCES))).all()
        return [enrich_player_metadata(player.raw_profile) for player in players if player.raw_profile]
    finally:
        if owns_session:
            db.close()


def replace_ingested_players(players: list[dict[str, Any]], db: Session | None = None) -> list[dict[str, Any]]:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        existing_players = db.scalars(select(Player).where(Player.source == PUBLIC_DATA_SOURCE)).all()
        existing_by_external_id = {player.external_id: player for player in existing_players}
        for player_data in players:
            player = existing_by_external_id.get(player_data['id'])
            if not player:
                player = Player(external_id=player_data['id'])
                db.add(player)

            player.name = player_data.get('name', '')
            player.position = player_data.get('position', '')
            player.club = player_data.get('club', '')
            player.nationality = player_data.get('nationality', '')
            player.age = player_data.get('age')
            player.estimated_value = player_data.get('estimatedValue', '')
            player.source = PUBLIC_DATA_SOURCE
            player.raw_profile = enrich_player_metadata(player_data)

        if owns_session:
            db.commit()
        else:
            db.flush()
    finally:
        if owns_session:
            db.close()

    return players
