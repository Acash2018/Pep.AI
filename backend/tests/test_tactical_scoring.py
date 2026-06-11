from app.data.mock_players import MOCK_PLAYERS
from app.services.role_matching import RoleMatchingService
from app.services.tactical_scoring import TacticalFitScoringService


def test_tactical_scoring_returns_bounded_score_and_reasoning():
    player = MOCK_PLAYERS[0]
    role_match = RoleMatchingService().match_role(player)
    score = TacticalFitScoringService().score_fit(
        player,
        'High press & quick transitions',
        role_match,
        [],
    )

    assert 0 <= score['score'] <= 100
    assert score['grade'] in {'Elite fit', 'Strong fit', 'Risky fit', 'Low fit'}
    assert score['why_fit']
    assert score['why_not']
    assert score['system_compatibility']['style_overlap_score'] > 0


def test_generic_trait_query_uses_custom_profile_instead_of_first_system():
    system = TacticalFitScoringService().identify_system(
        'Looking for a player with a good left foot and creative in midfield'
    )

    assert system['system_id'] == 'custom_profile'
    assert system['label'] == 'Custom Profile'
    assert {'chance creation', 'vision', 'passing'}.issubset(system['required_strengths'])
