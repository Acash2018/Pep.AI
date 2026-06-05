from app.services.metadata_retrieval import metadata_aware_player_search


def test_ball_playing_center_back_query_filters_out_attacking_midfielders():
    players = [
        {
            'id': 'cb1',
            'name': 'Build Up Defender',
            'position': 'Center Back',
            'club': 'Test FC',
            'age': 25,
            'nationality': 'Testland',
            'estimatedValue': 'EUR 10m',
            'summary': '',
            'strengths': ['passing', 'ball retention'],
            'weaknesses': ['pace'],
            'tacticalStyle': 'Back 3 buildup passing',
            'fitScore': 7,
            'reportHighlights': [],
            'stats': {'goals': 0, 'assists': 1, 'passAccuracy': 88},
        },
        {
            'id': 'am1',
            'name': 'Advanced Creator',
            'position': 'Attacking Midfielder',
            'club': 'Test FC',
            'age': 23,
            'nationality': 'Testland',
            'estimatedValue': 'EUR 20m',
            'summary': '',
            'strengths': ['passing', 'vision', 'chance creation'],
            'weaknesses': ['defensive work rate'],
            'tacticalStyle': 'Progressive central creation',
            'fitScore': 8,
            'reportHighlights': [],
            'stats': {'goals': 8, 'assists': 10, 'passAccuracy': 89},
        },
    ]

    results = metadata_aware_player_search('ball-playing center back in a back 3', players)

    assert [player['id'] for player in results] == ['cb1']
    assert results[0]['retrieval_metadata']['positional_confidence_score'] == 100
