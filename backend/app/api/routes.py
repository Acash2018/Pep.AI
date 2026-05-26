from fastapi import APIRouter, HTTPException
from app.services.players import get_all_players, search_players, get_player_by_id
from app.services.agents import generate_scouting_report, scout_player
from app.services.knowledge_base import knowledge_base_service
from app.services.statsbomb import ingest_statsbomb_players
from app.models import ReportRequest, ScoutPlayerRequest, ScoutPlayerResponse

router = APIRouter()

@router.get('/players')
def players():
    return {'players': get_all_players()}

@router.get('/players/search')
def players_search(q: str = ''):
    return {'players': search_players(q)}


@router.post('/players/ingest/statsbomb')
def ingest_statsbomb(max_matches: int = 6):
    try:
        return ingest_statsbomb_players(max_matches=max_matches)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Unable to ingest StatsBomb data: {exc}') from exc


@router.post('/knowledge/ingest')
def ingest_knowledge_base():
    try:
        return knowledge_base_service.ingest_knowledge_base()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get('/knowledge/search')
def search_knowledge(q: str, limit: int = 5):
    try:
        return {'results': knowledge_base_service.vector_search_service.search(q, limit)}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@router.get('/players/{player_id}')
def player_detail(player_id: str):
    player = get_player_by_id(player_id)
    if not player:
        raise HTTPException(status_code=404, detail='Player not found')
    return player

@router.post('/reports')
def create_report(request: ReportRequest):
    try:
        report = generate_scouting_report(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {'report': report}


@router.post('/scout-player', response_model=ScoutPlayerResponse)
def scout_player_endpoint(request: ScoutPlayerRequest):
    try:
        return scout_player(request)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
