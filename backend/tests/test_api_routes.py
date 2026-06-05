from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_ollama_status():
    with TestClient(app) as client:
        response = client.get('/api/health')

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'ok'
    assert 'available' in payload['ollama']
    assert 'model' in payload['ollama']


def test_players_endpoint_returns_mock_players():
    with TestClient(app) as client:
        response = client.get('/api/players')

    assert response.status_code == 200
    players = response.json()['players']
    assert {player['id'] for player in players} >= {'p1', 'p2'}


def test_scout_player_uses_cached_report_after_first_generation():
    request = {
        'player_id': 'p1',
        'club': 'Pep.AI XI',
        'preferred_system': 'High press & quick transitions',
    }

    with TestClient(app) as client:
        first = client.post('/api/scout-player', json={**request, 'force_refresh': True})
        second = client.post('/api/scout-player', json=request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()['cached'] is True
    assert second.json()['report']['final_report_markdown'].startswith('## Executive Summary')
