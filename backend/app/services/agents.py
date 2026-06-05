from dotenv import load_dotenv
from app.models import ReportRequest, ScoutPlayerRequest
from app.services.persistence import get_cached_scouting_result, persist_scouting_result
from app.services.workflow import scouting_graph

load_dotenv()

def scout_player(request: ScoutPlayerRequest) -> dict:
    if not getattr(request, 'force_refresh', False):
        cached = get_cached_scouting_result(request)
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
    return persist_scouting_result(request, payload)


def generate_scouting_report(request: ReportRequest) -> dict:
    return scout_player(
        ScoutPlayerRequest(
            player_id=request.player_id,
            club=request.club,
            preferred_system=request.preferred_system,
        )
    )
