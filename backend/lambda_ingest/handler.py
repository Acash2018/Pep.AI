import csv
import io
import json
import os
from datetime import datetime
from typing import Any
from urllib.parse import unquote_plus
from urllib.parse import urlparse

import boto3
import pg8000.dbapi

s3 = boto3.client('s3')
secretsmanager = boto3.client('secretsmanager')


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    database_config = _database_config()
    records = event.get('Records', [])
    total_ingested = 0
    objects = []

    with pg8000.dbapi.connect(**database_config) as conn:
        _ensure_players_table(conn)
        for record in records:
            bucket = record['s3']['bucket']['name']
            key = unquote_plus(record['s3']['object']['key'])
            players = _load_players(bucket, key)
            ingested = _upsert_players(conn, players, bucket, key)
            total_ingested += ingested
            objects.append({'bucket': bucket, 'key': key, 'players_ingested': ingested})

        conn.commit()

    return {
        'statusCode': 200,
        'objects': objects,
        'players_ingested': total_ingested,
    }


def _database_config() -> dict[str, Any]:
    secret_arn = os.environ['DATABASE_SECRET_ARN']
    secret = secretsmanager.get_secret_value(SecretId=secret_arn)['SecretString']
    parsed = urlparse(secret.replace('postgresql+psycopg://', 'postgresql://', 1))
    return {
        'user': parsed.username,
        'password': parsed.password,
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
    }


def _load_players(bucket: str, key: str) -> list[dict[str, Any]]:
    body = s3.get_object(Bucket=bucket, Key=key)['Body'].read().decode('utf-8-sig')
    lower_key = key.lower()
    if lower_key.endswith('.json'):
        payload = json.loads(body)
        if isinstance(payload, dict):
            payload = payload.get('players', [])
        if not isinstance(payload, list):
            raise ValueError('JSON ingestion files must contain a list or a {"players": [...]} object.')
        return [_normalize_player(row) for row in payload]

    if lower_key.endswith('.csv'):
        reader = csv.DictReader(io.StringIO(body))
        return [_normalize_player(row) for row in reader]

    raise ValueError(f'Unsupported ingestion file type for s3://{bucket}/{key}. Use .json or .csv.')


def _normalize_player(row: dict[str, Any]) -> dict[str, Any]:
    external_id = row.get('id') or row.get('external_id') or row.get('player_id')
    name = row.get('name') or row.get('player_name')
    if not external_id or not name:
        raise ValueError('Each player row must include id/external_id/player_id and name/player_name.')

    age = row.get('age')
    if age in ('', None):
        age = None
    else:
        age = int(age)

    profile = dict(row)
    profile['id'] = str(external_id)
    profile['name'] = str(name)
    profile['position'] = row.get('position', '')
    profile['club'] = row.get('club', '')
    profile['nationality'] = row.get('nationality', '')
    profile['age'] = age
    profile['estimatedValue'] = row.get('estimatedValue') or row.get('estimated_value') or ''
    profile['source'] = row.get('source') or 'S3 Upload'
    profile['summary'] = row.get('summary') or f"{profile['position'] or 'Player'} profile uploaded through S3."
    profile['strengths'] = _list_value(row.get('strengths')) or ['profile ingestion']
    profile['weaknesses'] = _list_value(row.get('weaknesses')) or ['sample size sensitivity']
    profile['tacticalStyle'] = row.get('tacticalStyle') or row.get('tactical_style') or 'Uploaded scouting profile'
    profile['fitScore'] = int(row.get('fitScore') or row.get('fit_score') or 5)
    profile['reportHighlights'] = _list_value(row.get('reportHighlights') or row.get('report_highlights')) or [
        'Uploaded through S3 ingestion',
    ]
    return profile


def _list_value(value: Any) -> list[str]:
    if value is None or value == '':
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split('|') if item.strip()]
    return [str(value)]


def _upsert_players(conn: pg8000.dbapi.Connection, players: list[dict[str, Any]], bucket: str, key: str) -> int:
    now = datetime.utcnow()
    cur = conn.cursor()
    try:
        for player in players:
            raw_profile = {
                **player,
                'ingestion': {
                    'bucket': bucket,
                    'key': key,
                    'ingested_at': now.isoformat(),
                },
            }
            cur.execute(
                """
                INSERT INTO players (
                    external_id, name, position, club, nationality, age,
                    estimated_value, source, raw_profile, created_at, updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s, %s
                )
                ON CONFLICT (external_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    position = EXCLUDED.position,
                    club = EXCLUDED.club,
                    nationality = EXCLUDED.nationality,
                    age = EXCLUDED.age,
                    estimated_value = EXCLUDED.estimated_value,
                    source = EXCLUDED.source,
                    raw_profile = EXCLUDED.raw_profile,
                    updated_at = EXCLUDED.updated_at
                """,
                (
                    player['id'],
                    player['name'],
                    player.get('position', ''),
                    player.get('club', ''),
                    player.get('nationality', ''),
                    player.get('age'),
                    player.get('estimatedValue', ''),
                    player.get('source', 'S3 Upload'),
                    json.dumps(raw_profile),
                    now,
                    now,
                ),
            )
    finally:
        cur.close()
    return len(players)


def _ensure_players_table(conn: pg8000.dbapi.Connection) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                external_id VARCHAR(120) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL DEFAULT '',
                position VARCHAR(120) NOT NULL DEFAULT '',
                club VARCHAR(255) NOT NULL DEFAULT '',
                nationality VARCHAR(120) NOT NULL DEFAULT '',
                age INTEGER,
                estimated_value VARCHAR(120) NOT NULL DEFAULT '',
                source VARCHAR(120) NOT NULL DEFAULT 'Pep.AI',
                raw_profile JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    finally:
        cur.close()
