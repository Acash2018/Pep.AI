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
    'false_nine': {
        'label': 'False 9',
        'keywords': {'false', 'nine', 'withdrawn', 'drop', 'link', 'central'},
        'aliases': {'false 9', 'false nine', 'false-9', 'false-nine'},
        'required_strengths': {'vision', 'passing', 'dribbling', 'ball retention', 'chance creation', 'finishing'},
        'risk_weaknesses': {'aerial duels', 'limited goal threat', 'defensive work rate'},
    },
    'tiki_taka': {
        'label': 'Tiki-Taka',
        'keywords': {'tiki', 'taka', 'possession', 'short', 'passing', 'triangles'},
        'aliases': {'tiki-taka', 'tiki taka', 'tikitaka'},
        'required_strengths': {'passing', 'ball retention', 'vision', 'positional discipline', 'dribbling'},
        'risk_weaknesses': {'vertical passing', 'passing security', 'defensive intensity', 'concentration'},
    },
    'total_football': {
        'label': 'Total Football',
        'keywords': {'total', 'football', 'rotation', 'fluid', 'positional', 'interchange'},
        'aliases': {'total football', 'totaalvoetbal'},
        'required_strengths': {'vision', 'passing', 'stamina', 'ball carrying', 'positional discipline'},
        'risk_weaknesses': {'concentration', 'defensive work rate', 'passing security'},
    },
    'direct_play': {
        'label': 'Direct Play',
        'keywords': {'direct', 'long', 'vertical', 'forward', 'route'},
        'aliases': {'direct play', 'direct football', 'route one', 'long ball'},
        'required_strengths': {'finishing', 'tackling', 'ball carrying', 'stamina', 'defensive coverage'},
        'risk_weaknesses': {'ball progression volume', 'passing security', 'concentration'},
    },
    'mid_block_pressing': {
        'label': 'Mid-Block Pressing',
        'keywords': {'mid', 'block', 'pressing', 'compact', 'shape'},
        'aliases': {'mid-block', 'mid block', 'mid-block press', 'mid block press'},
        'required_strengths': {'pressing', 'positional discipline', 'tackling', 'stamina', 'defensive coverage'},
        'risk_weaknesses': {'concentration', 'defensive work rate', 'defensive intensity'},
    },
    'back_three': {
        'label': 'Back Three System',
        'keywords': {'back', 'three', 'wing', 'back', 'libero', 'overload'},
        'aliases': {'back three', 'back-three', '3 at the back', 'three at the back', '3atb'},
        'required_strengths': {'tackling', 'defensive coverage', 'crossing', 'stamina', 'passing'},
        'risk_weaknesses': {'aerial duels', 'concentration', 'defensive intensity'},
    },
    'wing_play': {
        'label': 'Wing Play',
        'keywords': {'wing', 'play', 'wide', 'crossing', 'overlap'},
        'aliases': {'wing play', 'wing-play', 'crossing game', 'wide attack'},
        'required_strengths': {'crossing', 'stamina', 'dribbling', 'chance creation', 'ball carrying'},
        'risk_weaknesses': {'aerial duels', 'passing security', 'concentration'},
    },
    'catenaccio': {
        'label': 'Catenaccio',
        'keywords': {'catenaccio', 'sweeper', 'libero', 'compact', 'defensive'},
        'aliases': {'catenaccio', 'sweeper system'},
        'required_strengths': {'tackling', 'defensive coverage', 'positional discipline', 'finishing'},
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
            'why_fit': _why_fit(player, preferred_system, system, system_strength_matches, role_match, style_overlap),
            'why_not': _why_not(player, preferred_system, system, system_risks, role_match),
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
        return 'Risky fit'
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


RISK_CONSEQUENCES = {
    'passing security': "turnovers in build-up will repeatedly invite pressure into dangerous zones",
    'defensive work rate': "off-ball effort drops in repeat phases, leaving shape gaps for opponents to exploit",
    'concentration': "lapses during long defensive spells turn into clear chances against the block",
    'aerial duels': "set-pieces and direct balls become a recurring weak link",
    'vertical passing': "progression stalls when the system demands decisive forward passes",
    'defensive intensity': "pressing triggers go uncovered, breaking the press as a coordinated unit",
    'limited goal threat': "chance volume needs to be high because conversion will not bail the team out",
    'ball progression volume': "the side loses a vertical outlet through this position",
    'sample size sensitivity': "the projection rests on a thin sample and could regress under stronger opposition",
}


def _why_fit(
    player: dict,
    preferred_system: str,
    system: dict,
    matches: set[str],
    role_match: dict,
    style_overlap: int,
) -> list[str]:
    reasons: list[str] = []
    stats = player['stats']
    system_label = system['label']

    if matches:
        traits = sorted(matches)
        reasons.append(
            f"{_humanize_list(traits)} in the existing profile map directly onto {system_label}'s core demands."
        )

    primary = role_match['primary_role']
    matched_traits = list(primary.get('matched_traits') or [])
    if matched_traits:
        reasons.append(
            f"Profile fits the {primary['label']} role through {_humanize_list(matched_traits[:3])}, "
            f"so the staff has a defined in-system assignment from day one."
        )
    elif primary.get('score', 0) >= 60:
        reasons.append(
            f"Primary role projection ({primary['label']}) scores {primary['score']}/100 — a viable in-system home even without trait-level overlap."
        )

    stat_evidence = []
    if stats['assists'] >= 8:
        stat_evidence.append(f"{stats['assists']} assists carrying chance-creation responsibility")
    elif stats['assists'] >= 4:
        stat_evidence.append(f"{stats['assists']} assists as a secondary creator")
    if stats['goals'] >= 8:
        stat_evidence.append(f"{stats['goals']} goals as a direct end-product threat")
    elif stats['goals'] >= 4:
        stat_evidence.append(f"{stats['goals']} goals showing finishing involvement")
    if stats['passAccuracy'] >= 88:
        stat_evidence.append(f"{stats['passAccuracy']}% pass accuracy under pressure")
    elif stats['passAccuracy'] >= 84:
        stat_evidence.append(f"{stats['passAccuracy']}% pass accuracy as a reliable circulation baseline")
    if stat_evidence:
        reasons.append(f"Statistical signal supports the projection: {'; '.join(stat_evidence)}.")

    if style_overlap >= 2:
        reasons.append(
            f"Current style ({player['tacticalStyle']}) already overlaps with {preferred_system} — "
            f"cuts the tactical re-education the staff has to deliver."
        )

    age = player.get('age')
    if isinstance(age, int) and age <= 24 and matches:
        reasons.append(
            f"At {age}, the matched traits ({_humanize_list(sorted(matches))}) give a coachable base before any tactical ceiling."
        )

    if not reasons:
        reasons.append(
            f"Direct profile overlap with {system_label} is thin — the case rests on coaching projection rather than current evidence."
        )

    return reasons[:5]


def _why_not(
    player: dict,
    preferred_system: str,
    system: dict,
    risks: set[str],
    role_match: dict,
) -> list[str]:
    reasons: list[str] = []
    stats = player['stats']
    system_label = system['label']

    for risk in sorted(risks):
        consequence = RISK_CONSEQUENCES.get(
            risk,
            f"this trait conflicts directly with how {system_label} expects the role to be played",
        )
        reasons.append(f"{risk.capitalize()}: {consequence}.")

    player_strengths = {s.lower() for s in player['strengths']}
    missing = sorted(system['required_strengths'] - player_strengths)
    if missing:
        top_missing = missing[:3]
        reasons.append(
            f"Profile lacks {_humanize_list(top_missing)} — system-critical traits with no evidence in the current data."
        )

    if stats['goals'] < 5 and stats['assists'] < 5:
        reasons.append(
            f"Low final-third output in the sample ({stats['goals']}G / {stats['assists']}A) — "
            f"unclear whether the player can carry attacking responsibility at a higher level."
        )
    if stats['passAccuracy'] < 80:
        reasons.append(
            f"{stats['passAccuracy']}% pass accuracy is below the threshold for systems that demand sustained ball circulation."
        )

    primary = role_match['primary_role']
    if primary.get('score', 0) < 55:
        reasons.append(
            f"No strong in-system home: best role projection ({primary['label']}) only scores {primary['score']}/100."
        )

    style_terms = set(_normalize_text(player.get('tacticalStyle', '')).split())
    system_terms = set()
    for keyword in system['keywords']:
        system_terms.update(_normalize_text(keyword).split())
    if style_terms and system_terms and not style_terms.intersection(system_terms):
        reasons.append(
            f"Current style ({player['tacticalStyle']}) shares no vocabulary with {system_label} — "
            f"the staff will have to manage a meaningful tactical re-education."
        )

    if not reasons:
        reasons.append(
            'No specific tactical objection surfaced from the data — the main uncertainty is sample size and transferability.'
        )

    return reasons[:5]


def _humanize_list(items) -> str:
    items = [item for item in items if item]
    if not items:
        return ''
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"
