from typing import List, Optional

from app.data.player_repository import retrieve_all_player_data, retrieve_player_data
from app.services.role_matching import RoleMatchingService
from app.services.tactical_scoring import TacticalFitScoringService

_role_matcher = RoleMatchingService()
_tactical_scorer = TacticalFitScoringService()

GOALKEEPER_TOKENS = {'goalkeeper', 'keeper', 'gk'}
DEFENDER_TOKENS = {'back', 'defender'}
FORWARD_ONLY_SYSTEMS = {'false_nine'}


def get_all_players() -> List[dict]:
    return retrieve_all_player_data()


def get_player_by_id(player_id: str) -> Optional[dict]:
    return retrieve_player_data(player_id)


def search_players(query: str) -> List[dict]:
    normalized = query.strip().lower()
    if not normalized:
        return get_all_players()
    return [
        player
        for player in get_all_players()
        if normalized in player['name'].lower()
        or normalized in player['position'].lower()
        or normalized in player['club'].lower()
    ]


def _position_tokens(position: str) -> set[str]:
    return set(position.lower().replace('-', ' ').split())


def _position_compatible(position: str, system_id: str) -> bool:
    tokens = _position_tokens(position)
    if tokens & GOALKEEPER_TOKENS:
        return False
    if system_id in FORWARD_ONLY_SYSTEMS:
        if 'forward' in tokens or 'striker' in tokens or 'winger' in tokens:
            return True
        if 'attacking' in tokens and ('midfielder' in tokens or 'midfield' in tokens):
            return True
        return False
    return True


def scout_candidates_for_system(preferred_system: str, min_fit: int = 54) -> dict:
    identified = _tactical_scorer.identify_system(preferred_system)
    system_id = identified.get('system_id', '')
    system_label = identified.get('label', preferred_system)

    candidates = []
    total_evaluated = 0
    for player in get_all_players():
        if not _position_compatible(player['position'], system_id):
            continue
        total_evaluated += 1
        role_match = _role_matcher.match_role(player)
        score = _tactical_scorer.score_fit(player, preferred_system, role_match, [])
        if score['score'] < min_fit:
            continue
        candidates.append({
            **player,
            'systemFitScore': score['score'],
            'systemFitGrade': score['grade'],
            'systemMatchedPrinciples': score['system_compatibility']['matched_principles'],
        })

    candidates.sort(key=lambda p: p['systemFitScore'], reverse=True)
    return {
        'players': candidates,
        'system_label': system_label,
        'system_id': system_id,
        'evaluated': total_evaluated,
        'min_fit': min_fit,
    }
