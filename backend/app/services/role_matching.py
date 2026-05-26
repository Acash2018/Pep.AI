ROLE_ARCHETYPES = {
    'inverted_winger': {
        'label': 'Inverted Winger',
        'keywords': {'winger', 'wide', 'dribbling', 'finishing', 'chance creation', 'acceleration'},
    },
    'ball_progressor': {
        'label': 'Ball Progressor',
        'keywords': {'midfielder', 'full-back', 'wing-back', 'ball carrying', 'passing', 'vision', 'progression'},
    },
    'deep_lying_playmaker': {
        'label': 'Deep-Lying Playmaker',
        'keywords': {'midfielder', 'passing', 'vision', 'ball retention', 'positional discipline'},
    },
    'pressing_forward': {
        'label': 'Pressing Forward',
        'keywords': {'forward', 'pressing', 'finishing', 'work rate', 'stamina', 'acceleration'},
    },
}


class RoleMatchingService:
    def match_role(self, player: dict) -> dict:
        profile_terms = _profile_terms(player)
        matches = []

        for role_id, role in ROLE_ARCHETYPES.items():
            overlap = profile_terms.intersection(role['keywords'])
            raw_score = len(overlap)
            if role_id == 'ball_progressor' and player['stats']['passAccuracy'] >= 85:
                raw_score += 1
            if role_id == 'pressing_forward' and 'pressing' in player['strengths']:
                raw_score += 1

            matches.append(
                {
                    'role_id': role_id,
                    'label': role['label'],
                    'score': min(100, 35 + raw_score * 13),
                    'matched_traits': sorted(overlap),
                }
            )

        matches.sort(key=lambda item: item['score'], reverse=True)
        primary = matches[0]

        return {
            'primary_role': primary,
            'alternatives': matches[1:3],
        }


def _profile_terms(player: dict) -> set[str]:
    position_terms = set(player['position'].lower().replace('-', ' ').split())
    style_terms = set(player['tacticalStyle'].lower().replace('&', ' ').replace('-', ' ').split())
    strengths = {strength.lower() for strength in player['strengths']}
    return position_terms.union(style_terms).union(strengths)
