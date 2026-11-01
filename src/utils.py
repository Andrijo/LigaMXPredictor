"""
utils.py
--------
Funciones auxiliares compartidas entre módulos.
"""

import pandas as pd

# 18 equipos a una sola vuelta: 18 * 17 / 2 partidos de fase regular por torneo.
REGULAR_SEASON_MATCHES = 153
LIGUILLA_TEAMS = 8


def current_tournament(matches: pd.DataFrame) -> pd.DataFrame:
    """Partidos del torneo más reciente: el Clausura va de enero a junio y el
    Apertura de julio a diciembre."""
    last_date = matches["date"].max()
    start = pd.Timestamp(year=last_date.year, month=1 if last_date.month < 7 else 7, day=1)
    return matches[matches["date"] >= start]


def tournament_name(matches: pd.DataFrame) -> str:
    """Nombre del torneo más reciente, ej. 'Apertura 2026'."""
    last_date = matches["date"].max()
    return f"{'Clausura' if last_date.month < 7 else 'Apertura'} {last_date.year}"


def standings(tournament: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla general de un torneo (puntos, diferencia de goles, goles a favor).
    Solo cuenta la fase regular: la liguilla no suma a la tabla. No conoce
    sanciones administrativas de puntos, si las hubiera.
    """
    regular = tournament.sort_values("date", kind="mergesort").head(REGULAR_SEASON_MATCHES)

    home = pd.DataFrame({
        "Equipo": regular["home_team"], "GF": regular["home_score"], "GC": regular["away_score"],
    })
    away = pd.DataFrame({
        "Equipo": regular["away_team"], "GF": regular["away_score"], "GC": regular["home_score"],
    })
    games = pd.concat([home, away], ignore_index=True)
    games["G"] = (games["GF"] > games["GC"]).astype(int)
    games["E"] = (games["GF"] == games["GC"]).astype(int)
    games["P"] = (games["GF"] < games["GC"]).astype(int)
    games["PJ"] = 1

    table = games.groupby("Equipo")[["PJ", "G", "E", "P", "GF", "GC"]].sum().reset_index()
    table["DG"] = table["GF"] - table["GC"]
    table["Pts"] = table["G"] * 3 + table["E"]

    table = table.sort_values(["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)
    table.index += 1
    table.index.name = "Pos"
    return table


def get_team_list(matches: pd.DataFrame) -> list[str]:
    """Lista ordenada de todos los equipos presentes en el dataset."""
    teams = pd.unique(matches[["home_team", "away_team"]].values.ravel())
    return sorted(teams.tolist())


def head_to_head(matches: pd.DataFrame, team_a: str, team_b: str) -> pd.DataFrame:
    """Historial de enfrentamientos directos entre dos equipos."""
    mask = (
        ((matches["home_team"] == team_a) & (matches["away_team"] == team_b))
        | ((matches["home_team"] == team_b) & (matches["away_team"] == team_a))
    )
    return matches[mask].sort_values("date", ascending=False)


def recent_form(matches: pd.DataFrame, team: str, n: int = 5) -> pd.DataFrame:
    """Últimos n partidos jugados por un equipo (local o visitante)."""
    mask = (matches["home_team"] == team) | (matches["away_team"] == team)
    return matches[mask].sort_values("date", ascending=False).head(n)
