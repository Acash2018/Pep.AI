from copy import deepcopy

POSITION_TAXONOMY = {
    'GK': {'goalkeeper', 'keeper'},
    'CB': {'center back', 'centre back', 'central defender', 'defender', 'cb'},
    'LCB': {'left center back', 'left centre back', 'lcb'},
    'RCB': {'right center back', 'right centre back', 'rcb'},
    'LB': {'left back', 'left-back', 'lb'},
    'RB': {'right back', 'right-back', 'rb'},
    'LWB': {'left wing-back', 'left wing back', 'lwb', 'wing-back'},
    'RWB': {'right wing-back', 'right wing back', 'rwb', 'wing-back'},
    'DM': {'defensive midfielder', 'holding midfielder', 'pivot', 'dm'},
    'CM': {'central midfielder', 'center midfielder', 'midfielder', 'cm'},
    'AM': {'attacking midfielder', 'advanced playmaker', 'cam', 'number 10'},
    'LW': {'left winger', 'left wing', 'lw', 'inverted winger'},
    'RW': {'right winger', 'right wing', 'rw', 'inverted winger'},
    'ST': {'striker', 'forward', 'centre forward', 'center forward', 'pressing forward', 'st'},
}

POSITION_FAMILIES = {
    'GK': 'goalkeeper',
    'CB': 'center_back',
    'LCB': 'center_back',
    'RCB': 'center_back',
    'LB': 'fullback',
    'RB': 'fullback',
    'LWB': 'wingback',
    'RWB': 'wingback',
    'DM': 'midfield',
    'CM': 'midfield',
    'AM': 'attacking_midfield',
    'LW': 'wide_forward',
    'RW': 'wide_forward',
    'ST': 'forward',
}

ROLE_HIERARCHY = {
    'ball_playing_center_back': {
        'positions': {'CB', 'LCB', 'RCB'},
        'adjacent_positions': {'DM', 'LB', 'RB'},
        'keywords': {'ball-playing', 'ball playing', 'center back', 'centre back', 'buildup', 'build-up', 'progression', 'passing'},
    },
    'defensive_progressor': {
        'positions': {'CB', 'LCB', 'RCB', 'DM', 'LB', 'RB'},
        'adjacent_positions': {'CM', 'LWB', 'RWB'},
        'keywords': {'defensive progression', 'progressive defender', 'buildup passing', 'build-up passing'},
    },
    'ball_progressor': {
        'positions': {'DM', 'CM', 'AM', 'LB', 'RB', 'LWB', 'RWB'},
        'adjacent_positions': {'CB', 'LCB', 'RCB'},
        'keywords': {'ball progressor', 'progression', 'carrying', 'line-breaking', 'line breaking'},
    },
    'advanced_playmaker': {
        'positions': {'AM', 'CM', 'LW', 'RW'},
        'adjacent_positions': {'ST'},
        'keywords': {'advanced playmaker', 'chance creation', 'number 10', 'cam', 'creative midfielder'},
    },
    'pressing_forward': {
        'positions': {'ST', 'LW', 'RW'},
        'adjacent_positions': {'AM'},
        'keywords': {'pressing forward', 'forward press', 'counter press', 'gegenpressing striker'},
    },
    'inverted_winger': {
        'positions': {'LW', 'RW'},
        'adjacent_positions': {'AM', 'ST'},
        'keywords': {'inverted winger', 'inside forward', 'cut inside'},
    },
}

FORMATION_COMPATIBILITY = {
    'back_3': {'CB', 'LCB', 'RCB', 'LWB', 'RWB', 'DM'},
    'back_4': {'CB', 'LB', 'RB', 'DM', 'CM'},
    'double_pivot': {'DM', 'CM'},
    'front_3': {'LW', 'RW', 'ST'},
    'midfield_box': {'DM', 'CM', 'AM'},
}


def enrich_player_metadata(player: dict) -> dict:
    enriched = deepcopy(player)
    primary_position = infer_primary_position(enriched.get('position', ''))
    tactical_roles = infer_tactical_roles(enriched, primary_position)
    suitable_formations = infer_suitable_formations(primary_position, tactical_roles)

    enriched.update(
        {
            'primary_position': primary_position,
            'secondary_positions': infer_secondary_positions(primary_position),
            'position_family': POSITION_FAMILIES.get(primary_position, 'unknown'),
            'tactical_roles': tactical_roles,
            'suitable_formations': suitable_formations,
            'defensive_line_type': infer_defensive_line_type(enriched, primary_position),
            'progression_profile': infer_progression_profile(enriched, primary_position),
            'pressing_profile': infer_pressing_profile(enriched),
            'tactical_archetype': infer_tactical_archetype(enriched, primary_position, tactical_roles),
        }
    )
    return enriched


def infer_primary_position(position: str) -> str:
    normalized = normalize_text(position)
    best_code = 'CM'
    best_length = 0
    for code, aliases in POSITION_TAXONOMY.items():
        for alias in aliases:
            if normalize_text(alias) in normalized and len(alias) > best_length:
                best_code = code
                best_length = len(alias)
    return best_code


def infer_query_constraints(query: str) -> dict:
    normalized = normalize_text(query)
    requested_positions = set()
    requested_roles = set()
    requested_formations = set()

    for code, aliases in POSITION_TAXONOMY.items():
        if any(normalize_text(alias) in normalized for alias in aliases):
            requested_positions.add(code)

    if 'back 3' in normalized or 'back three' in normalized or 'three at the back' in normalized:
        requested_formations.add('back_3')
        requested_positions.update({'CB', 'LCB', 'RCB'})
    if 'back 4' in normalized or 'back four' in normalized or 'four at the back' in normalized:
        requested_formations.add('back_4')
    if 'double pivot' in normalized:
        requested_formations.add('double_pivot')

    for role_id, role in ROLE_HIERARCHY.items():
        if any(normalize_text(keyword) in normalized for keyword in role['keywords']):
            requested_roles.add(role_id)
            requested_positions.update(role['positions'])

    return {
        'positions': requested_positions,
        'roles': requested_roles,
        'formations': requested_formations,
        'query_terms': set(normalized.split()),
    }


def infer_tactical_roles(player: dict, primary_position: str) -> list[str]:
    strengths = {normalize_text(strength) for strength in player.get('strengths', [])}
    stats = player.get('stats', {})
    roles = []

    if primary_position in {'CB', 'LCB', 'RCB'} and (stats.get('passAccuracy', 0) >= 82 or 'passing' in strengths or 'ball retention' in strengths):
        roles.append('ball_playing_center_back')
    if primary_position in {'CB', 'LCB', 'RCB', 'DM', 'LB', 'RB'} and ('passing' in strengths or 'ball carrying' in strengths or stats.get('passAccuracy', 0) >= 84):
        roles.append('defensive_progressor')
    if 'vision' in strengths or 'passing' in strengths or 'ball carrying' in strengths:
        roles.append('ball_progressor')
    if primary_position in {'AM', 'CM', 'LW', 'RW'} and ('chance creation' in strengths or 'vision' in strengths):
        roles.append('advanced_playmaker')
    if primary_position in {'ST', 'LW', 'RW'} and ('pressing' in strengths or 'stamina' in strengths):
        roles.append('pressing_forward')
    if primary_position in {'LW', 'RW'} and 'dribbling' in strengths:
        roles.append('inverted_winger')

    return roles or ['balanced_role']


def infer_secondary_positions(primary_position: str) -> list[str]:
    adjacency = {
        'CB': ['LCB', 'RCB'],
        'LCB': ['CB', 'LB'],
        'RCB': ['CB', 'RB'],
        'DM': ['CM', 'CB'],
        'CM': ['DM', 'AM'],
        'AM': ['CM', 'LW', 'RW'],
        'LWB': ['LB', 'LW'],
        'RWB': ['RB', 'RW'],
        'ST': ['LW', 'RW'],
    }
    return adjacency.get(primary_position, [])


def infer_suitable_formations(primary_position: str, tactical_roles: list[str]) -> list[str]:
    formations = [
        formation
        for formation, positions in FORMATION_COMPATIBILITY.items()
        if primary_position in positions
    ]
    if 'ball_playing_center_back' in tactical_roles and 'back_3' not in formations:
        formations.append('back_3')
    return formations or ['general_structure']


def infer_defensive_line_type(player: dict, primary_position: str) -> str:
    style = normalize_text(player.get('tacticalStyle', ''))
    if 'press' in style or 'high' in style:
        return 'high_line'
    if primary_position in {'CB', 'LCB', 'RCB', 'DM'}:
        return 'mid_block_or_adaptive'
    return 'not_primary_defensive_line'


def infer_progression_profile(player: dict, primary_position: str) -> str:
    strengths = {normalize_text(strength) for strength in player.get('strengths', [])}
    if primary_position in {'CB', 'LCB', 'RCB'} and ('passing' in strengths or player.get('stats', {}).get('passAccuracy', 0) >= 82):
        return 'defensive_progression'
    if 'ball carrying' in strengths or 'dribbling' in strengths:
        return 'carry_progression'
    if 'passing' in strengths or 'vision' in strengths:
        return 'buildup_passing'
    return 'limited_progression_evidence'


def infer_pressing_profile(player: dict) -> str:
    strengths = {normalize_text(strength) for strength in player.get('strengths', [])}
    style = normalize_text(player.get('tacticalStyle', ''))
    if 'pressing' in strengths or 'press' in style or 'stamina' in strengths:
        return 'active_presser'
    if 'defensive work rate' in {normalize_text(weakness) for weakness in player.get('weaknesses', [])}:
        return 'pressing_risk'
    return 'neutral_pressing_profile'


def infer_tactical_archetype(player: dict, primary_position: str, tactical_roles: list[str]) -> str:
    if 'ball_playing_center_back' in tactical_roles:
        return 'Ball-playing defender'
    if 'advanced_playmaker' in tactical_roles:
        return 'Creative final-third connector'
    if 'pressing_forward' in tactical_roles:
        return 'Front-line pressing attacker'
    if primary_position in {'LWB', 'RWB'}:
        return 'Progressive wing-back'
    if 'ball_progressor' in tactical_roles:
        return 'Ball progression hub'
    return 'Balanced tactical profile'


def normalize_text(text: str) -> str:
    return text.lower().replace('-', ' ').replace('&', ' and ')
