from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import ReportRequest, ScoutPlayerRequest
from app.services.persistence import get_cached_scouting_result, persist_scouting_result
from app.services.workflow import scouting_graph

load_dotenv()

def scout_player(request: ScoutPlayerRequest, db: Session | None = None) -> dict:
    owns_session = db is None
    db = db or SessionLocal()
    try:
        return _scout_player_with_session(request, db)
    finally:
        if owns_session:
            db.close()


def _scout_player_with_session(request: ScoutPlayerRequest, db: Session) -> dict:
    if not getattr(request, 'force_refresh', False):
        cached = get_cached_scouting_result(db, request)
        if cached:
            return cached

    final_state = scouting_graph.invoke(
        {
            'player_id': request.player_id,
            'buying_club': request.club,
            'preferred_system': request.preferred_system,
        }
    )

    report = final_state['report']
    payload = {
        'player': final_state['player'],
        'strengths': report['strengths'],
        'weaknesses': report['weaknesses'],
        'tactical_fit': final_state['tactical_fit'],
        'transfer_value': final_state['transfer_value'],
        'similar_players': final_state['similar_players'],
        'report': report,
    }
    return persist_scouting_result(db, request, payload)


def generate_scouting_report(request: ReportRequest, db: Session | None = None) -> dict:
    return scout_player(
        ScoutPlayerRequest(
            player_id=request.player_id,
            club=request.club,
            preferred_system=request.preferred_system,
        ),
        db=db,
    )
