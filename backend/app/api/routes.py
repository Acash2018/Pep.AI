from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.players import get_all_players, search_players, get_player_by_id, scout_candidates_for_system
from app.services.agents import generate_scouting_report, scout_player
from app.services.knowledge_base import knowledge_base_service
from app.services.persistence import (
    HistoryPersistenceService,
    PlayerPersistenceService,
    ScoutingReportPersistenceService,
    serialize_report,
)
from app.services.statsbomb import ingest_statsbomb_players
from app.models import ReportRequest, ScoutPlayerRequest, ScoutPlayerResponse

router = APIRouter()

@router.get('/players')
def players():
    return {'players': get_all_players()}

@router.get('/players/search')
def players_search(q: str = '', db: Session = Depends(get_db)):
    results = search_players(q)
    HistoryPersistenceService(db).record_search(q, len(results))
    db.commit()
    return {'players': results}


@router.get('/players/scout-candidates')
def players_scout_candidates(system: str, min_fit: int = 54):
    if not system.strip():
        raise HTTPException(status_code=400, detail='system query parameter is required')
    return scout_candidates_for_system(system, min_fit=min_fit)


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


@router.get('/memory/players')
def analyzed_players(limit: int = 50, db: Session = Depends(get_db)):
    players = PlayerPersistenceService(db).get_analyzed_players(limit)
    return {'players': [player.raw_profile | {'databaseId': player.id} for player in players]}


@router.get('/memory/players/{player_id}/timeline')
def player_timeline(player_id: str, db: Session = Depends(get_db)):
    timeline = PlayerPersistenceService(db).timeline(player_id)
    if not timeline:
        raise HTTPException(status_code=404, detail='No saved analysis for player')
    return timeline


@router.get('/memory/reports')
def saved_reports(limit: int = 50, db: Session = Depends(get_db)):
    reports = ScoutingReportPersistenceService(db).list_reports(limit)
    return {'reports': [serialize_report(report) for report in reports]}


@router.get('/memory/comparisons/{player_id}')
def saved_comparisons(player_id: str, db: Session = Depends(get_db)):
    return {'comparisons': HistoryPersistenceService(db).comparison_history(player_id)}

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
