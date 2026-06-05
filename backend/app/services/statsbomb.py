import json
from collections import Counter, defaultdict
from typing import Any
from urllib.request import urlopen

from app.data.dynamic_players import replace_ingested_players
from app.services.football_metadata import enrich_player_metadata
from sqlalchemy.orm import Session

BASE_URL = 'https://raw.githubusercontent.com/statsbomb/open-data/master/data'
DEFAULT_COMPETITION_ID = 9
DEFAULT_SEASON_ID = 281


def ingest_statsbomb_players(max_matches: int = 6, min_events: int = 12, db: Session | None = None) -> dict[str, Any]:
    matches = _fetch_json(f'{BASE_URL}/matches/{DEFAULT_COMPETITION_ID}/{DEFAULT_SEASON_ID}.json')
    selected_matches = matches[:max_matches]

    player_profiles: dict[int, dict[str, Any]] = {}
    player_stats: dict[int, dict[str, int]] = defaultdict(
        lambda: {
            'goals': 0,
            'assists': 0,
            'passes': 0,
            'completed_passes': 0,
            'shots': 0,
            'carries': 0,
            'pressures': 0,
            'events': 0,
        }
    )

    for match in selected_matches:
        match_id = match['match_id']
        _merge_lineups(player_profiles, _fetch_json(f'{BASE_URL}/lineups/{match_id}.json'))
        _merge_events(player_profiles, player_stats, _fetch_json(f'{BASE_URL}/events/{match_id}.json'))

    players = _build_players(player_profiles, player_stats, min_events)
    replace_ingested_players(players, db=db)
    if db is not None:
        db.commit()

    return {
        'source': 'StatsBomb Open Data',
        'competition': '1. Bundesliga',
        'season': '2023/2024',
        'matches_ingested': len(selected_matches),
        'players_ingested': len(players),
        'players': players,
    }


def _fetch_json(url: str) -> Any:
    with urlopen(url, timeout=20) as response:
        return json.loads(response.read().decode('utf-8'))


def _merge_lineups(player_profiles: dict[int, dict[str, Any]], lineups: list[dict]) -> None:
    for team in lineups:
        for player in team.get('lineup', []):
            player_id = player['player_id']
            positions = [entry['position'] for entry in player.get('positions', [])]
            profile = player_profiles.setdefault(
                player_id,
                {
                    'player_id': player_id,
                    'name': player.get('player_nickname') or player['player_name'],
                    'club': team['team_name'],
                    'nationality': player.get('country', {}).get('name', 'Unknown'),
                    'positions': Counter(),
                },
            )
            profile['club'] = team['team_name']
            profile['positions'].update(positions)


def _merge_events(
    player_profiles: dict[int, dict[str, Any]],
    player_stats: dict[int, dict[str, int]],
    events: list[dict],
) -> None:
    for event in events:
        player = event.get('player')
        if not player:
            continue

        player_id = player['id']
        stats = player_stats[player_id]
        stats['events'] += 1

        player_profiles.setdefault(
            player_id,
            {
                'player_id': player_id,
                'name': player['name'],
                'club': event.get('team', {}).get('name', 'Unknown'),
                'nationality': 'Unknown',
                'positions': Counter(),
            },
        )

        event_type = event.get('type', {}).get('name')
        if event_type == 'Pass':
            stats['passes'] += 1
            if 'outcome' not in event.get('pass', {}):
                stats['completed_passes'] += 1
            if event.get('pass', {}).get('goal_assist'):
                stats['assists'] += 1
        elif event_type == 'Shot':
            stats['shots'] += 1
            if event.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
                stats['goals'] += 1
        elif event_type == 'Carry':
            stats['carries'] += 1
        elif event_type == 'Pressure':
            stats['pressures'] += 1


def _build_players(
    player_profiles: dict[int, dict[str, Any]],
    player_stats: dict[int, dict[str, int]],
    min_events: int,
) -> list[dict]:
    players = []
    for player_id, profile in player_profiles.items():
        stats = player_stats[player_id]
        if stats['events'] < min_events:
            continue

        position = _primary_position(profile['positions'])
        pass_accuracy = round((stats['completed_passes'] / stats['passes']) * 100) if stats['passes'] else 0
        strengths = _infer_strengths(position, stats, pass_accuracy)
        weaknesses = _infer_weaknesses(position, stats, pass_accuracy)
        fit_score = _fit_score(stats, pass_accuracy)

        players.append(
            enrich_player_metadata({
                'id': f"sb-{player_id}",
                'name': profile['name'],
                'position': position,
                'club': profile['club'],
                'age': 24,
                'nationality': profile['nationality'],
                'estimatedValue': _estimate_value(stats, fit_score),
                'summary': f"StatsBomb profile built from {stats['events']} event actions in the public Bundesliga sample.",
                'strengths': strengths,
                'weaknesses': weaknesses,
                'tacticalStyle': _tactical_style(position, stats),
                'fitScore': fit_score,
                'reportHighlights': _highlights(stats, pass_accuracy),
                'stats': {
                    'goals': stats['goals'],
                    'assists': stats['assists'],
                    'passAccuracy': pass_accuracy,
                },
                'source': 'StatsBomb Open Data',
            })
        )

    return sorted(players, key=lambda player: (player['fitScore'], player['stats']['assists'], player['stats']['goals']), reverse=True)


def _primary_position(positions: Counter) -> str:
    if not positions:
        return 'Unknown'
    return positions.most_common(1)[0][0]


def _infer_strengths(position: str, stats: dict[str, int], pass_accuracy: int) -> list[str]:
    strengths = []
    if stats['goals'] > 0:
        strengths.append('finishing')
    if stats['assists'] > 0:
        strengths.append('chance creation')
    if pass_accuracy >= 86:
        strengths.append('ball retention')
    if stats['carries'] >= 10:
        strengths.append('ball carrying')
    if stats['pressures'] >= 8:
        strengths.append('pressing')
    if 'Back' in position and 'defensive coverage' not in strengths:
        strengths.append('defensive coverage')
    return strengths[:4] or ['involvement', 'positional discipline']


def _infer_weaknesses(position: str, stats: dict[str, int], pass_accuracy: int) -> list[str]:
    weaknesses = []
    if pass_accuracy < 78:
        weaknesses.append('passing security')
    if stats['goals'] == 0 and any(term in position for term in ['Forward', 'Attacking']):
        weaknesses.append('limited goal threat')
    if stats['pressures'] < 4:
        weaknesses.append('defensive intensity')
    if stats['carries'] < 5:
        weaknesses.append('ball progression volume')
    return weaknesses[:3] or ['sample size sensitivity']


def _fit_score(stats: dict[str, int], pass_accuracy: int) -> int:
    score = 5
    if pass_accuracy >= 85:
        score += 1
    if stats['assists'] > 0:
        score += 1
    if stats['goals'] > 0:
        score += 1
    if stats['pressures'] >= 8:
        score += 1
    if stats['carries'] >= 10:
        score += 1
    return min(score, 10)


def _estimate_value(stats: dict[str, int], fit_score: int) -> str:
    value = 8 + (fit_score * 4) + (stats['goals'] * 5) + (stats['assists'] * 4)
    return f'EUR {value}m'


def _tactical_style(position: str, stats: dict[str, int]) -> str:
    if stats['pressures'] >= 8:
        return 'High press & quick transitions'
    if 'Wing Back' in position or stats['carries'] >= 10:
        return 'Wide build-up and overlapping runs'
    if stats['passes'] >= 30:
        return 'Possession-based circulation'
    return 'Balanced team structure'


def _highlights(stats: dict[str, int], pass_accuracy: int) -> list[str]:
    return [
        f"{stats['goals']} goals and {stats['assists']} assists in sample",
        f"{pass_accuracy}% pass accuracy",
        f"{stats['carries']} carries and {stats['pressures']} pressures",
    ]
