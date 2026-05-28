from typing import Optional

from app.data.dynamic_players import get_ingested_players
from app.data.mock_players import MOCK_PLAYERS
from app.services.football_metadata import enrich_player_metadata


def retrieve_all_player_data() -> list[dict]:
    return [enrich_player_metadata(player) for player in MOCK_PLAYERS + get_ingested_players()]


def retrieve_player_data(player_id: str) -> Optional[dict]:
    return next((player for player in retrieve_all_player_data() if player['id'] == player_id), None)


def retrieve_similar_players(player: dict, limit: int = 3) -> list[dict]:
    position_terms = set(player['position'].lower().replace('-', ' ').split())

    candidates = []
    for candidate in retrieve_all_player_data():
        if candidate['id'] == player['id']:
            continue

        candidate_terms = set(candidate['position'].lower().replace('-', ' ').split())
        shared_strengths = set(player['strengths']).intersection(candidate['strengths'])
        position_overlap = len(position_terms.intersection(candidate_terms))

        candidates.append((position_overlap + len(shared_strengths), candidate))

    ranked = sorted(candidates, key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in ranked[:limit]]
