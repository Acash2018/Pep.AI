from typing import Any, List

from pydantic import BaseModel


class ReportRequest(BaseModel):
    player_id: str
    club: str
    preferred_system: str


class ScoutPlayerRequest(BaseModel):
    player_id: str
    club: str = ''
    preferred_system: str


class ScoutPlayerResponse(BaseModel):
    player: dict[str, Any]
    strengths: List[str]
    weaknesses: List[str]
    tactical_fit: dict[str, Any]
    transfer_value: str
    similar_players: List[dict[str, Any]]
    report: dict[str, Any]
    memory: dict[str, Any] | None = None
    cached: bool | None = None
