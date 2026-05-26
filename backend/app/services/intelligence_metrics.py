def consistency_score(player: dict) -> int:
    stats = player.get('stats', {})
    pass_accuracy = stats.get('passAccuracy', 0)
    strengths = len(player.get('strengths', []))
    weaknesses = len(player.get('weaknesses', []))
    score = 45 + min(35, pass_accuracy // 3) + strengths * 4 - weaknesses * 3
    return _clamp(score)


def risk_profile_score(player: dict, tactical_fit: dict) -> int:
    weaknesses = len(player.get('weaknesses', []))
    tactical_risks = len(tactical_fit.get('system_compatibility', {}).get('risk_factors', []))
    fit_score = tactical_fit.get('fit_score', 0)
    score = 25 + weaknesses * 10 + tactical_risks * 12 + max(0, 70 - fit_score) // 2
    return _clamp(score)


def scouting_confidence_score(player: dict, tactical_fit: dict, similar_players: list[dict]) -> int:
    stats = player.get('stats', {})
    evidence_points = 0
    evidence_points += 1 if stats.get('passAccuracy', 0) else 0
    evidence_points += 1 if tactical_fit.get('retrieved_knowledge') else 0
    evidence_points += 1 if tactical_fit.get('role_match') else 0
    evidence_points += 1 if similar_players else 0
    evidence_points += 1 if player.get('source') else 0
    return _clamp(45 + evidence_points * 10)


def development_trajectory_notes(player: dict, tactical_fit: dict) -> str:
    strengths = player.get('strengths', [])[:2]
    weaknesses = player.get('weaknesses', [])[:2]
    score = tactical_fit.get('fit_score', 0)

    if score >= 80:
        trajectory = 'ready to contribute quickly if role demands stay close to current strengths'
    elif score >= 60:
        trajectory = 'development path depends on targeted adaptation work'
    else:
        trajectory = 'requires a longer tactical adaptation runway'

    return (
        f"Trajectory: {trajectory}. Build around {', '.join(strengths) or 'current strengths'} "
        f"while monitoring {', '.join(weaknesses) or 'role-specific risks'}."
    )


def _clamp(score: int) -> int:
    return max(0, min(100, int(score)))
