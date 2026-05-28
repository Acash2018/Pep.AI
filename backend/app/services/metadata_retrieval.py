from app.services.football_metadata import (
    FORMATION_COMPATIBILITY,
    ROLE_HIERARCHY,
    enrich_player_metadata,
    infer_query_constraints,
    normalize_text,
)


def metadata_aware_player_search(query: str, players: list[dict]) -> list[dict]:
    enriched_players = [enrich_player_metadata(player) for player in players]
    normalized_query = normalize_text(query.strip())
    if not normalized_query:
        return enriched_players

    constraints = infer_query_constraints(normalized_query)
    filtered_players = _hard_filter(enriched_players, constraints)
    ranked_players = sorted(
        (
            {
                **player,
                'retrieval_metadata': score_player_relevance(player, normalized_query, constraints),
            }
            for player in filtered_players
        ),
        key=lambda player: player['retrieval_metadata']['weighted_score'],
        reverse=True,
    )
    return ranked_players


def score_player_relevance(player: dict, query: str, constraints: dict) -> dict:
    position_confidence = _position_confidence(player, constraints)
    role_overlap = _role_overlap(player, constraints)
    formation_score = _formation_score(player, constraints)
    lexical_score = _lexical_score(player, query)
    tactical_relevance = _tactical_relevance(player, query, constraints)
    unrelated_penalty = _unrelated_position_penalty(player, constraints)

    weighted_score = (
        position_confidence * 0.34
        + tactical_relevance * 0.24
        + role_overlap * 0.18
        + formation_score * 0.14
        + lexical_score * 0.10
        - unrelated_penalty
    )

    return {
        'positional_confidence_score': max(0, min(100, int(position_confidence))),
        'tactical_relevance_score': max(0, min(100, int(tactical_relevance))),
        'role_overlap_score': max(0, min(100, int(role_overlap))),
        'formation_compatibility_score': max(0, min(100, int(formation_score))),
        'lexical_score': max(0, min(100, int(lexical_score))),
        'unrelated_position_penalty': unrelated_penalty,
        'weighted_score': max(0, min(100, int(weighted_score))),
    }


def _hard_filter(players: list[dict], constraints: dict) -> list[dict]:
    if not constraints['positions'] and not constraints['formations'] and not constraints['roles']:
        return players

    filtered = []
    for player in players:
        positions = {player['primary_position'], *player.get('secondary_positions', [])}

        if constraints['positions'] and not positions.intersection(constraints['positions']):
            if not _has_allowed_role_adjacency(player, constraints):
                continue

        if constraints['formations'] and not set(player.get('suitable_formations', [])).intersection(constraints['formations']):
            formation_positions = set().union(*(FORMATION_COMPATIBILITY[formation] for formation in constraints['formations']))
            if not positions.intersection(formation_positions):
                continue

        if constraints['roles'] and not set(player.get('tactical_roles', [])).intersection(constraints['roles']):
            if not _has_allowed_role_adjacency(player, constraints):
                continue

        filtered.append(player)

    return filtered


def _has_allowed_role_adjacency(player: dict, constraints: dict) -> bool:
    positions = {player['primary_position'], *player.get('secondary_positions', [])}
    for role_id in constraints['roles']:
        role = ROLE_HIERARCHY.get(role_id)
        if not role:
            continue
        if positions.intersection(role['adjacent_positions']) and _defensive_role_context(role_id, player):
            return True
    return False


def _defensive_role_context(role_id: str, player: dict) -> bool:
    if role_id in {'ball_playing_center_back', 'defensive_progressor'}:
        return player['primary_position'] in {'CB', 'LCB', 'RCB', 'DM', 'LB', 'RB'}
    return True


def _position_confidence(player: dict, constraints: dict) -> int:
    if not constraints['positions']:
        return 65
    positions = {player['primary_position'], *player.get('secondary_positions', [])}
    if player['primary_position'] in constraints['positions']:
        return 100
    if positions.intersection(constraints['positions']):
        return 78
    if _has_allowed_role_adjacency(player, constraints):
        return 55
    return 0


def _role_overlap(player: dict, constraints: dict) -> int:
    if not constraints['roles']:
        return 55
    overlap = set(player.get('tactical_roles', [])).intersection(constraints['roles'])
    if overlap:
        return min(100, 65 + len(overlap) * 25)
    if _has_allowed_role_adjacency(player, constraints):
        return 45
    return 0


def _formation_score(player: dict, constraints: dict) -> int:
    if not constraints['formations']:
        return 55
    overlap = set(player.get('suitable_formations', [])).intersection(constraints['formations'])
    return 100 if overlap else 0


def _lexical_score(player: dict, query: str) -> int:
    searchable = normalize_text(
        ' '.join(
            [
                player.get('name', ''),
                player.get('position', ''),
                player.get('club', ''),
                player.get('tacticalStyle', ''),
                player.get('tactical_archetype', ''),
                ' '.join(player.get('strengths', [])),
                ' '.join(player.get('tactical_roles', [])),
            ]
        )
    )
    query_terms = set(query.split())
    if not query_terms:
        return 0
    return int((len(query_terms.intersection(searchable.split())) / len(query_terms)) * 100)


def _tactical_relevance(player: dict, query: str, constraints: dict) -> int:
    score = 35
    if 'defensive' in query and player.get('progression_profile') == 'defensive_progression':
        score += 25
    if ('buildup' in query or 'build' in query or 'passing' in query) and player.get('progression_profile') in {'defensive_progression', 'buildup_passing'}:
        score += 25
    if 'press' in query and player.get('pressing_profile') == 'active_presser':
        score += 15
    score += _role_overlap(player, constraints) // 5
    return min(100, score)


def _unrelated_position_penalty(player: dict, constraints: dict) -> int:
    if not constraints['positions']:
        return 0
    positions = {player['primary_position'], *player.get('secondary_positions', [])}
    if positions.intersection(constraints['positions']) or _has_allowed_role_adjacency(player, constraints):
        return 0
    return 45
