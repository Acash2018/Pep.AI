from typing import Any, TypedDict


class ScoutState(TypedDict, total=False):
    player_id: str
    buying_club: str
    preferred_system: str
    player: dict[str, Any]
    stats_analysis: dict[str, Any]
    tactical_fit: dict[str, Any]
    role_match: dict[str, Any]
    tactical_score: dict[str, Any]
    retrieved_knowledge: list[dict[str, Any]]
    report: dict[str, Any]
    similar_players: list[dict[str, Any]]
    transfer_value: str
