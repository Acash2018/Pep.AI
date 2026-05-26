SYSTEM_ARCHETYPES = {
    'angeball': {
        'label': 'Angeball',
        'keywords': {'angeball', 'aggressive', 'wide', 'transition', 'press', 'forward', 'runs'},
        'aliases': {'angeball', 'ange', 'postecoglou'},
        'required_strengths': {'stamina', 'passing', 'ball carrying', 'pressing', 'chance creation'},
        'risk_weaknesses': {'defensive work rate', 'concentration', 'passing security'},
    },
    'pep_positional_play': {
        'label': 'Pep Positional Play',
        'keywords': {'pep', 'positional', 'possession', 'control', 'circulation', 'zones'},
        'aliases': {'pep', 'positional play', 'possession play', 'possession-based', 'possession based'},
        'required_strengths': {'vision', 'passing', 'ball retention', 'positional discipline', 'dribbling'},
        'risk_weaknesses': {'vertical passing', 'passing security', 'defensive intensity'},
    },
    'low_block_counter': {
        'label': 'Low Block Counter',
        'keywords': {'low', 'block', 'counter', 'compact', 'transition', 'direct'},
        'aliases': {'low block', 'low-block', 'counter attack', 'counter-attack', 'counter attacking'},
        'required_strengths': {'stamina', 'tackling', 'defensive coverage', 'finishing', 'ball carrying'},
        'risk_weaknesses': {'concentration', 'aerial duels', 'defensive work rate'},
    },
    'gegenpressing': {
        'label': 'Gegenpressing',
        'keywords': {'gegenpressing', 'press', 'counter-press', 'counter', 'transition', 'intensity'},
        'aliases': {'gegenpressing', 'gegenpress', 'high press', 'counter press', 'counter-press', 'pressing'},
        'required_strengths': {'pressing', 'stamina', 'tackling', 'chance creation', 'ball retention'},
        'risk_weaknesses': {'defensive work rate', 'concentration', 'passing security'},
    },
}


class TacticalFitScoringService:
    def score_fit(self, player: dict, preferred_system: str, role_match: dict, retrieved_context: list[dict]) -> dict:
        system = self.identify_system(preferred_system)
        player_strengths = {strength.lower() for strength in player['strengths']}
        player_weaknesses = {weakness.lower() for weakness in player['weaknesses']}
        stats = player['stats']

        system_strength_matches = player_strengths.intersection(system['required_strengths'])
        system_risks = player_weaknesses.intersection(system['risk_weaknesses'])
        style_overlap = _word_overlap(preferred_system, player['tacticalStyle'])

        score = 45
        score += len(system_strength_matches) * 9
        score += min(style_overlap, 4) * 5
        score += max(0, role_match['primary_role']['score'] - 50) // 4
        score += 6 if stats['passAccuracy'] >= 86 else 0
        score += 5 if stats['assists'] >= 8 else 0
        score += 4 if stats['goals'] >= 8 else 0
        score += min(len(retrieved_context), 4) * 2
        score -= len(system_risks) * 8
        score = max(0, min(100, int(score)))

        return {
            'score': score,
            'grade': _grade(score),
            'system': system['label'],
            'system_id': system['system_id'],
            'system_compatibility': {
                'matched_principles': sorted(system_strength_matches),
                'risk_factors': sorted(system_risks),
                'style_overlap_score': style_overlap,
            },
            'tactical_strengths': _tactical_strengths(player, system_strength_matches, role_match),
            'tactical_weaknesses': _tactical_weaknesses(player, system_risks),
            'why_fit': _why_fit(player, preferred_system, system_strength_matches, role_match),
            'why_not': _why_not(player, system_risks),
        }

    def identify_system(self, preferred_system: str) -> dict:
        normalized_query = _normalize_text(preferred_system)
        query_terms = set(normalized_query.split())
        best_id = 'pep_positional_play'
        best_overlap = -1

        for system_id, system in SYSTEM_ARCHETYPES.items():
            if any(_normalize_text(alias) in normalized_query for alias in system['aliases']):
                return {'system_id': system_id, **system}

            overlap = len(query_terms.intersection(system['keywords']))
            if overlap > best_overlap:
                best_id = system_id
                best_overlap = overlap

        return {'system_id': best_id, **SYSTEM_ARCHETYPES[best_id]}


def _word_overlap(first: str, second: str) -> int:
    first_terms = set(_normalize_text(first).split())
    second_terms = set(_normalize_text(second).split())
    return len(first_terms.intersection(second_terms))


def _normalize_text(text: str) -> str:
    normalized = text.lower().replace('&', ' and ').replace('-', ' ')
    words = []
    for word in normalized.split():
        if word.endswith('ing') and len(word) > 5:
            words.append(word)
        elif word.endswith('s') and not word.endswith('ss') and len(word) > 4:
            words.append(word[:-1])
        else:
            words.append(word)
    return ' '.join(words)


def _grade(score: int) -> str:
    if score >= 85:
        return 'Elite fit'
    if score >= 70:
        return 'Strong fit'
    if score >= 55:
        return 'Conditional fit'
    return 'Low fit'


def _tactical_strengths(player: dict, matches: set[str], role_match: dict) -> list[str]:
    strengths = [f"{trait} maps directly to the target system" for trait in sorted(matches)]
    strengths.append(f"Best role projection: {role_match['primary_role']['label']}")
    if player['stats']['passAccuracy'] >= 86:
        strengths.append('Secure possession profile supports repeatable tactical execution')
    return strengths[:5]


def _tactical_weaknesses(player: dict, risks: set[str]) -> list[str]:
    weaknesses = [f"{risk} could reduce system reliability" for risk in sorted(risks)]
    if player['stats']['goals'] < 5:
        weaknesses.append('Limited goal output lowers final-third ceiling')
    if not weaknesses:
        weaknesses.append('No major tactical red flag from the current profile')
    return weaknesses[:4]


def _why_fit(player: dict, preferred_system: str, matches: set[str], role_match: dict) -> list[str]:
    reasons = [
        f"{player['name']} has {', '.join(sorted(matches)) or 'general profile traits'} that align with {preferred_system}.",
        f"The {role_match['primary_role']['label']} projection gives the staff a clear tactical usage path.",
    ]
    if player['stats']['assists'] > 0:
        reasons.append('Existing assist production supports chance creation responsibilities.')
    return reasons


def _why_not(player: dict, risks: set[str]) -> list[str]:
    if not risks:
        return ['The main uncertainty is sample size and transferability to a stronger tactical environment.']
    return [f"{risk} is a tactical adaptation risk." for risk in sorted(risks)]
