from app.services.workflow import scouting_graph


def test_langgraph_scouting_workflow_smoke():
    state = scouting_graph.invoke(
        {
            'player_id': 'p2',
            'buying_club': 'Pep.AI XI',
            'preferred_system': 'Low block counter',
        }
    )

    assert state['player']['id'] == 'p2'
    assert state['stats_analysis']['agent'] == 'Stats Agent'
    assert state['tactical_fit']['agent'] == 'Tactical Fit Agent'
    assert state['report']['agent'] == 'Report Writer Agent'
    assert state['report']['final_report_markdown'].startswith('## Executive Summary')
