from typing import List, Optional

from app.data.player_repository import retrieve_all_player_data, retrieve_player_data


def get_all_players() -> List[dict]:
    return retrieve_all_player_data()


def get_player_by_id(player_id: str) -> Optional[dict]:
    return retrieve_player_data(player_id)


def search_players(query: str) -> List[dict]:
    normalized = query.strip().lower()
    if not normalized:
        return get_all_players()
    return [
        player
        for player in get_all_players()
        if normalized in player['name'].lower()
        or normalized in player['position'].lower()
        or normalized in player['club'].lower()
    ]
