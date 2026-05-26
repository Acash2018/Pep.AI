INGESTED_PLAYERS: list[dict] = []


def get_ingested_players() -> list[dict]:
    return INGESTED_PLAYERS


def replace_ingested_players(players: list[dict]) -> list[dict]:
    INGESTED_PLAYERS.clear()
    INGESTED_PLAYERS.extend(players)
    return INGESTED_PLAYERS
