from app.data.player_repository import retrieve_all_player_data


class PlayerComparisonEngine:
    def find_similar_players(self, player: dict, limit: int = 3) -> list[dict]:
        comparisons = []
        for candidate in retrieve_all_player_data():
            if candidate['id'] == player['id']:
                continue

            score, reasons = self.compare(player, candidate)
            comparisons.append(
                {
                    **candidate,
                    'similarityScore': score,
                    'similarityReasons': reasons,
                }
            )

        comparisons.sort(key=lambda item: item['similarityScore'], reverse=True)
        return comparisons[:limit]

    def compare(self, player: dict, candidate: dict) -> tuple[int, list[str]]:
        score = 0
        reasons = []

        if _position_family(player['position']) == _position_family(candidate['position']):
            score += 25
            reasons.append('same position family')

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

        return min(score, 100), reasons or ['nearest available profile in the current data pool']


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
