from app.data.player_repository import retrieve_all_player_data
from app.db.models import Player
from app.db.session import SessionLocal
from app.services.football_metadata import enrich_player_metadata
from app.services.intelligence_metrics import risk_profile_score
from app.services.metadata_retrieval import score_player_relevance


class PlayerComparisonEngine:
    def find_similar_players(self, player: dict, limit: int = 3) -> list[dict]:
        comparisons = []
        for candidate in _comparison_pool():
            if candidate['id'] == player['id']:
                continue

            score, reasons, matrix = self.compare(enrich_player_metadata(player), enrich_player_metadata(candidate))
            comparisons.append(
                {
                    **candidate,
                    'similarityScore': score,
                    'similarityReasons': reasons,
                    'attributeSimilarity': matrix['attribute_similarity'],
                    'tacticalSimilarityScore': matrix['tactical_suitability']['score'],
                    'riskDelta': matrix['risk_profile']['risk_delta'],
                    'stylisticOverlap': matrix['stylistic_overlap'],
                    'strengthWeaknessMatrix': matrix['strengths_weaknesses'],
                    'comparisonMatrix': matrix,
                }
            )

        comparisons.sort(key=lambda item: item['similarityScore'], reverse=True)
        return comparisons[:limit]

    def compare(self, player: dict, candidate: dict) -> tuple[int, list[str], dict]:
        score = 0
        reasons = []
        position_relation = _position_relation(player, candidate)

        if position_relation == 'same_primary':
            score += 35
            reasons.append('same primary position')
        elif position_relation == 'same_family':
            score += 25
            reasons.append('same position family')
        elif position_relation == 'role_adjacent':
            score += 12
            reasons.append('role-adjacent position')
        else:
            score -= 35
            reasons.append('unrelated position penalty')

        shared_strengths = set(player['strengths']).intersection(candidate['strengths'])
        if shared_strengths:
            score += min(30, len(shared_strengths) * 10)
            reasons.append(f"shared strengths: {', '.join(sorted(shared_strengths))}")

        style_overlap = _overlap(player['tacticalStyle'], candidate['tacticalStyle'])
        if style_overlap:
            score += min(20, style_overlap * 5)
            reasons.append('similar tactical style language')

        pass_gap = abs(player['stats']['passAccuracy'] - candidate['stats']['passAccuracy'])
        if pass_gap <= 5:
            score += 10
            reasons.append('similar pass security')

        output_gap = abs((player['stats']['goals'] + player['stats']['assists']) - (candidate['stats']['goals'] + candidate['stats']['assists']))
        if output_gap <= 5:
            score += 15
            reasons.append('similar attacking output')

        metadata_relevance = score_player_relevance(
            candidate,
            f"{player['primary_position']} {' '.join(player.get('tactical_roles', []))} {' '.join(player.get('suitable_formations', []))}",
            {
                'positions': {player['primary_position']},
                'roles': set(player.get('tactical_roles', [])),
                'formations': set(player.get('suitable_formations', [])),
                'query_terms': set(),
            },
        )
        matrix = _comparison_matrix(player, candidate)
        matrix['metadata_relevance'] = metadata_relevance
        score = min(100, int((score * 0.55) + (matrix['overall_matrix_score'] * 0.45)))

        return min(score, 100), reasons or ['nearest available profile in the current data pool'], matrix


def _comparison_matrix(player: dict, candidate: dict) -> dict:
    shared_strengths = sorted(set(player['strengths']).intersection(candidate['strengths']))
    player_unique_strengths = sorted(set(player['strengths']).difference(candidate['strengths']))
    candidate_unique_strengths = sorted(set(candidate['strengths']).difference(player['strengths']))
    shared_weaknesses = sorted(set(player['weaknesses']).intersection(candidate['weaknesses']))

    pass_gap = abs(player['stats']['passAccuracy'] - candidate['stats']['passAccuracy'])
    output_gap = abs(_output(player) - _output(candidate))
    style_overlap = _overlap(player['tacticalStyle'], candidate['tacticalStyle'])
    tactical_score = min(100, style_overlap * 18 + len(shared_strengths) * 12 + (20 if _position_family(player['position']) == _position_family(candidate['position']) else 0))
    player_risk = risk_profile_score(player, {'fit_score': player.get('fitScore', 60), 'system_compatibility': {'risk_factors': []}})
    candidate_risk = risk_profile_score(candidate, {'fit_score': candidate.get('fitScore', 60), 'system_compatibility': {'risk_factors': []}})

    attribute_similarity = {
        'primary_position': player.get('primary_position'),
        'candidate_primary_position': candidate.get('primary_position'),
        'position_family_match': _position_family(player['position']) == _position_family(candidate['position']),
        'pass_accuracy_gap': pass_gap,
        'output_gap': output_gap,
        'age_gap': abs((player.get('age') or 0) - (candidate.get('age') or 0)),
    }
    attribute_score = 0
    attribute_score += 25 if attribute_similarity['position_family_match'] else 0
    attribute_score += max(0, 25 - pass_gap * 3)
    attribute_score += max(0, 25 - output_gap * 3)
    attribute_score += max(0, 25 - attribute_similarity['age_gap'] * 4)

    return {
        'attribute_similarity': attribute_similarity,
        'tactical_suitability': {
            'score': tactical_score,
            'style_overlap_terms': style_overlap,
            'player_style': player['tacticalStyle'],
            'candidate_style': candidate['tacticalStyle'],
        },
        'risk_profile': {
            'player_risk': player_risk,
            'candidate_risk': candidate_risk,
            'risk_delta': abs(player_risk - candidate_risk),
            'shared_weaknesses': shared_weaknesses,
        },
        'stylistic_overlap': {
            'score': min(100, style_overlap * 20),
            'shared_strengths': shared_strengths,
        },
        'strengths_weaknesses': {
            'shared_strengths': shared_strengths,
            'player_unique_strengths': player_unique_strengths,
            'candidate_unique_strengths': candidate_unique_strengths,
            'shared_weaknesses': shared_weaknesses,
        },
        'overall_matrix_score': min(100, int((attribute_score * 0.35) + (tactical_score * 0.35) + (max(0, 100 - abs(player_risk - candidate_risk)) * 0.30))),
    }


def _position_family(position: str) -> str:
    lower = position.lower()
    if 'forward' in lower or 'winger' in lower or 'attacking' in lower:
        return 'attacker'
    if 'midfielder' in lower or 'midfield' in lower:
        return 'midfielder'
    if 'back' in lower or 'defender' in lower:
        return 'defender'
    return lower


def _overlap(first: str, second: str) -> int:
    first_terms = set(first.lower().replace('&', ' ').replace('-', ' ').split())
    second_terms = set(second.lower().replace('&', ' ').replace('-', ' ').split())
    return len(first_terms.intersection(second_terms))


def _output(player: dict) -> int:
    stats = player.get('stats', {})
    return stats.get('goals', 0) + stats.get('assists', 0)


def _position_relation(player: dict, candidate: dict) -> str:
    if player.get('primary_position') == candidate.get('primary_position'):
        return 'same_primary'
    player_positions = {player.get('primary_position'), *player.get('secondary_positions', [])}
    candidate_positions = {candidate.get('primary_position'), *candidate.get('secondary_positions', [])}
    if player_positions.intersection(candidate_positions):
        return 'role_adjacent'
    if player.get('position_family') == candidate.get('position_family'):
        return 'same_family'
    return 'unrelated'


def _comparison_pool() -> list[dict]:
    pool_by_id = {player['id']: player for player in retrieve_all_player_data()}
    try:
        with SessionLocal() as db:
            for player in db.query(Player).all():
                if player.raw_profile:
                    pool_by_id[player.external_id] = enrich_player_metadata(player.raw_profile)
    except Exception:
        pass
    return list(pool_by_id.values())
