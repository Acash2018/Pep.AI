from typing import List, Optional

from app.data.player_repository import retrieve_all_player_data, retrieve_player_data
from app.services.metadata_retrieval import metadata_aware_player_search
from app.services.role_matching import RoleMatchingService
from app.services.tactical_scoring import TacticalFitScoringService

_role_matcher = RoleMatchingService()
_tactical_scorer = TacticalFitScoringService()

GOALKEEPER_TOKENS = {'goalkeeper', 'keeper', 'gk'}
FORWARD_ONLY_SYSTEMS = {'false_nine'}

POSITION_FAMILIES = (
    'goalkeeper',
    'center_back',
    'full_back',
    'defensive_midfielder',
    'central_midfielder',
    'attacking_midfielder',
    'winger',
    'forward',
)

QUERY_POSITION_KEYWORDS: dict[str, tuple[str, ...]] = {
    'goalkeeper': ('goalkeeper', 'goalie', 'keeper'),
    'center_back': (
        'ball playing center back',
        'ball-playing center back',
        'ball playing centre back',
        'ball-playing centre back',
        'center back',
        'centre back',
        'central defender',
        'centre half',
        'center half',
    ),
    'full_back': (
        'wing back',
        'wing-back',
        'wingback',
        'full back',
        'full-back',
        'fullback',
        'left back',
        'left-back',
        'right back',
        'right-back',
    ),
    'defensive_midfielder': (
        'defensive midfielder',
        'defensive midfield',
        'holding midfielder',
        'holding midfield',
        'number 6',
        'no. 6',
        'cdm',
    ),
    'attacking_midfielder': (
        'attacking midfielder',
        'attacking midfield',
        'number 10',
        'no. 10',
        'playmaker',
        'cam',
    ),
    'central_midfielder': (
        'central midfielder',
        'central midfield',
        'box to box',
        'box-to-box',
        'box-to-box midfielder',
    ),
    'winger': (
        'winger',
        'wide forward',
        'wide attacker',
        'left wing',
        'right wing',
    ),
    'forward': (
        'center forward',
        'centre forward',
        'striker',
        'target man',
        'false 9',
        'false nine',
        'number 9',
        'no. 9',
    ),
}


def get_all_players() -> List[dict]:
    return retrieve_all_player_data()


def get_player_by_id(player_id: str) -> Optional[dict]:
    return retrieve_player_data(player_id)


def search_players(query: str) -> List[dict]:
    normalized = query.strip().lower()
    if not normalized:
        return get_all_players()
    return metadata_aware_player_search(query, get_all_players())


def _position_tokens(position: str) -> set[str]:
    return set(position.lower().replace('-', ' ').split())


def _player_position_family(position: str) -> Optional[str]:
    p = position.lower().replace('-', ' ')
    tokens = set(p.split())
    if tokens & GOALKEEPER_TOKENS:
        return 'goalkeeper'
    if 'wing' in tokens and 'back' in tokens:
        return 'full_back'
    if 'forward' in tokens or 'striker' in tokens:
        return 'forward'
    if 'wing' in tokens:
        return 'winger'
    if 'attacking' in tokens and ('midfield' in tokens or 'midfielder' in tokens):
        return 'attacking_midfielder'
    if 'defensive' in tokens and ('midfield' in tokens or 'midfielder' in tokens):
        return 'defensive_midfielder'
    if 'center' in tokens and 'back' in tokens:
        return 'center_back'
    if 'centre' in tokens and 'back' in tokens:
        return 'center_back'
    if 'midfield' in tokens or 'midfielder' in tokens:
        return 'central_midfielder'
    if 'back' in tokens or 'defender' in tokens:
        return 'full_back'
    return None


def _extract_position_requirements(query: str) -> set[str]:
    q = ' ' + query.lower() + ' '
    required: set[str] = set()
    for family, phrases in QUERY_POSITION_KEYWORDS.items():
        for phrase in phrases:
            if f' {phrase} ' in q or q.startswith(phrase + ' ') or q.endswith(' ' + phrase):
                required.add(family)
                break
    return required


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


def _passes_position_filter(position: str, required_families: set[str], system_id: str) -> bool:
    if required_families:
        return _player_position_family(position) in required_families
    return _position_compatible(position, system_id)


def scout_candidates_for_system(preferred_system: str, min_fit: int = 54) -> dict:
    identified = _tactical_scorer.identify_system(preferred_system)
    system_id = identified.get('system_id', '')
    system_label = identified.get('label', preferred_system)
    required_families = _extract_position_requirements(preferred_system)

    candidates = []
    total_evaluated = 0
    for player in get_all_players():
        if not _passes_position_filter(player['position'], required_families, system_id):
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
        'required_position_families': sorted(required_families),
    }
