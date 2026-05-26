import os
from dotenv import load_dotenv
from app.models import ReportRequest, ScoutPlayerRequest
from app.services.workflow import scouting_graph

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def scout_player(request: ScoutPlayerRequest) -> dict:
    final_state = scouting_graph.invoke(
        {
            'player_id': request.player_id,
            'buying_club': request.club,
            'preferred_system': request.preferred_system,
        }
    )

    report = final_state['report']
    return {
        'player': final_state['player'],
        'strengths': report['strengths'],
        'weaknesses': report['weaknesses'],
        'tactical_fit': final_state['tactical_fit'],
        'transfer_value': final_state['transfer_value'],
        'similar_players': final_state['similar_players'],
        'report': report,
    }


def generate_scouting_report(request: ReportRequest) -> dict:
    return scout_player(
        ScoutPlayerRequest(
            player_id=request.player_id,
            club=request.club,
            preferred_system=request.preferred_system,
        )
    )
