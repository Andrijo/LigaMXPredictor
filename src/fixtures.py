"""
fixtures.py
-----------
Calendario de lo que falta de la fase regular.

El CSV de resultados no trae partidos futuros y puede ir unos días atrás, así
que los completamos con el marcador público de ESPN. No es una API oficial ni
documentada: solo acepta un día por consulta y puede cambiar sin aviso. Por eso
se usa solo para los cruces pendientes y, si falla, se sigue con la última copia
local. Si el calendario queda incompleto, quien lo use debe saberlo: ver
missing_fixtures().

Un torneo es a una sola vuelta, así que los cruces pendientes son los que aún
no aparecen en los resultados. Lo que no se puede deducir es la localía, porque
el Apertura se sortea de nuevo cada temporada.
"""

from itertools import combinations
from pathlib import Path
import time

import pandas as pd
import requests

from src.data_loader import MAX_DATA_AGE_HOURS, PROCESSED_DIR
from src.utils import LEAGUE_TEAMS, REGULAR_SEASON_MATCHES

ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/mex.1/scoreboard"
FIXTURES_FILENAME = "liga_mx_fixtures.csv"
MAX_SCAN_DAYS = 60

ESPN_TEAM_NAMES = {
    "Atlético de San Luis": "Atlético San Luis",
    "Guadalajara": "Chivas",
    "Pumas UNAM": "Pumas",
    "Tigres UANL": "Tigres",
}

FIXTURE_COLS = ["date", "home_team", "away_team", "home_score", "away_score"]
FETCH_ERRORS = (requests.RequestException, ValueError, KeyError, IndexError, TypeError)


def pending_matchups(tournament: pd.DataFrame) -> set[frozenset]:
    """Cruces de fase regular sin resultado. Requiere que ya hayan aparecido los
    18 equipos: en la primera jornada aún no se conoce la lista completa."""
    regular = tournament.sort_values("date", kind="mergesort").head(REGULAR_SEASON_MATCHES)
    teams = set(regular["home_team"]) | set(regular["away_team"])
    if len(teams) < LEAGUE_TEAMS:
        return set()
    played = {frozenset(pair) for pair in zip(regular["home_team"], regular["away_team"])}
    return {frozenset(pair) for pair in combinations(sorted(teams), 2)} - played


def parse_events(payload: dict) -> list[dict]:
    """Convierte la respuesta de ESPN al esquema de partidos del proyecto.
    Un partido sin terminar queda con marcador vacío."""
    rows = []
    for event in payload.get("events", []):
        sides = {side["homeAway"]: side for side in event["competitions"][0]["competitors"]}
        home_name = sides["home"]["team"]["displayName"]
        away_name = sides["away"]["team"]["displayName"]
        completed = event["status"]["type"]["completed"]
        rows.append({
            "date": pd.Timestamp(event["date"]).tz_localize(None).normalize(),
            "home_team": ESPN_TEAM_NAMES.get(home_name, home_name),
            "away_team": ESPN_TEAM_NAMES.get(away_name, away_name),
            "home_score": int(sides["home"]["score"]) if completed else None,
            "away_score": int(sides["away"]["score"]) if completed else None,
        })
    return rows


def fetch_fixtures(tournament: pd.DataFrame, pending: set[frozenset]) -> pd.DataFrame:
    """Recorre ESPN día por día desde el último resultado conocido, hasta
    encontrar todos los cruces pendientes o llegar a MAX_SCAN_DAYS."""
    found: dict[frozenset, dict] = {}
    session = requests.Session()
    first_day = tournament["date"].max()

    for offset in range(MAX_SCAN_DAYS):
        day = first_day + pd.Timedelta(days=offset)
        response = session.get(ESPN_SCOREBOARD_URL, params={"dates": f"{day:%Y%m%d}"}, timeout=20)
        response.raise_for_status()

        for row in parse_events(response.json()):
            matchup = frozenset((row["home_team"], row["away_team"]))
            if matchup in pending:
                found[matchup] = row

        if len(found) == len(pending):
            break

    return pd.DataFrame(list(found.values()), columns=FIXTURE_COLS)


def _read_local_copy(path: Path) -> pd.DataFrame:
    if path.exists():
        return pd.read_csv(path, parse_dates=["date"])
    return pd.DataFrame(columns=FIXTURE_COLS)


def _keep_pending(fixtures: pd.DataFrame, pending: set[frozenset]) -> pd.DataFrame:
    """Quita partidos que ya llegaron al CSV de resultados."""
    is_pending = [
        frozenset(pair) in pending
        for pair in zip(fixtures["home_team"], fixtures["away_team"])
    ]
    return fixtures.loc[is_pending].reset_index(drop=True)


def load_fixtures(tournament: pd.DataFrame, max_age_hours: float = MAX_DATA_AGE_HOURS) -> pd.DataFrame:
    """Partidos pendientes del torneo; con marcador si ya se jugaron. Si no se
    puede consultar ESPN, usa la última copia local aunque haya caducado."""
    pending = pending_matchups(tournament)
    if not pending:
        return pd.DataFrame(columns=FIXTURE_COLS)

    path = PROCESSED_DIR / FIXTURES_FILENAME
    is_fresh = path.exists() and (time.time() - path.stat().st_mtime) / 3600 <= max_age_hours
    if is_fresh:
        return _keep_pending(_read_local_copy(path), pending)

    try:
        fixtures = fetch_fixtures(tournament, pending)
    except FETCH_ERRORS as exc:
        print(f"No se pudo actualizar el calendario, usando copia local: {exc}")
        return _keep_pending(_read_local_copy(path), pending)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    fixtures.to_csv(path, index=False)
    return fixtures


def missing_fixtures(tournament: pd.DataFrame, fixtures: pd.DataFrame) -> int:
    """Cuántos cruces pendientes no tienen partido en el calendario."""
    found = {frozenset(pair) for pair in zip(fixtures["home_team"], fixtures["away_team"])}
    return len(pending_matchups(tournament) - found)


def played_fixtures(fixtures: pd.DataFrame) -> pd.DataFrame:
    """Partidos terminados que todavía no están en el CSV de resultados."""
    return fixtures.dropna(subset=["home_score", "away_score"]).astype({"home_score": int, "away_score": int})


def scheduled_fixtures(fixtures: pd.DataFrame) -> pd.DataFrame:
    """Partidos por jugarse."""
    return fixtures[fixtures["home_score"].isna()].reset_index(drop=True)


def with_played_fixtures(tournament: pd.DataFrame, fixtures: pd.DataFrame) -> pd.DataFrame:
    """Resultados del torneo más los que ESPN ya tiene y el CSV todavía no."""
    played = played_fixtures(fixtures)
    if played.empty:
        return tournament
    return pd.concat([tournament, played], ignore_index=True)
