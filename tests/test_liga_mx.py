import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import requests

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import data_loader
from src.backtest import walk_forward_backtest
from src.ensemble import EnsemblePredictor
from src.league_config import LIGA_MX, LIGA_MX_ALTITUDE_TEAMS, TEAM_NAMES
from src.liguilla import _LegSampler, simulate_liguilla, simulate_series
from src.utils import (
    REGULAR_SEASON_MATCHES,
    current_tournament,
    recent_window,
    standings,
    tournament_name,
)

CURRENT_TEAMS = {
    "Atlante", "Atlas", "Atlético San Luis", "América", "Chivas", "Cruz Azul",
    "FC Juárez", "León", "Monterrey", "Necaxa", "Pachuca", "Puebla", "Pumas",
    "Querétaro", "Santos", "Tigres", "Tijuana", "Toluca",
}


def raw_row(date, home, away, hg, ag):
    return {
        "Season": "2026/2027", "Date": date, "Home": home, "Away": away, "HG": hg, "AG": ag,
        "AvgCH": 2.0, "AvgCD": 3.5, "AvgCA": 4.0,
    }


def match(date, home, away, hs, a_s):
    return {
        "date": pd.Timestamp(date), "home_team": home, "away_team": away,
        "home_score": hs, "away_score": a_s,
    }


# --- data_loader ---------------------------------------------------------

def test_clean_data_reads_day_first_dates():
    """02/07/2022 es 2 de julio; leído al revés caería en febrero."""
    clean = data_loader.clean_data(pd.DataFrame([raw_row("02/07/2022", "Pachuca", "Toluca", 1, 0)]))
    assert clean.loc[0, "date"] == pd.Timestamp("2022-07-02")


def test_clean_data_normalizes_team_names():
    clean = data_loader.clean_data(pd.DataFrame([raw_row("02/07/2022", "Club America", "Guadalajara Chivas", 2, 1)]))
    assert clean.loc[0, "home_team"] == "América"
    assert clean.loc[0, "away_team"] == "Chivas"
    assert clean.loc[0, "result"] == 1


def test_clean_data_drops_unplayed_matches():
    raw = pd.DataFrame([
        raw_row("02/07/2022", "Pachuca", "Toluca", 1, 0),
        raw_row("09/07/2022", "Toluca", "Pachuca", None, None),
    ])
    assert len(data_loader.clean_data(raw)) == 1


def test_altitude_teams_use_normalized_names():
    """Un nombre sin normalizar haría que el bonus no aplique, sin ningún error."""
    assert set(LIGA_MX_ALTITUDE_TEAMS) <= CURRENT_TEAMS
    assert not set(LIGA_MX_ALTITUDE_TEAMS) & set(TEAM_NAMES)


def test_load_processed_falls_back_to_local_copy_when_offline(tmp_path, monkeypatch):
    monkeypatch.setattr(data_loader, "PROCESSED_DIR", tmp_path)
    clean = data_loader.clean_data(pd.DataFrame([raw_row("02/07/2022", "Pachuca", "Toluca", 1, 0)]))
    data_loader.save_processed(clean)

    def offline(*args, **kwargs):
        raise requests.ConnectionError("sin red")

    monkeypatch.setattr(data_loader, "refresh_data", offline)

    # max_age_hours negativo: la copia local siempre cuenta como caducada
    loaded = data_loader.load_processed(max_age_hours=-1)
    assert len(loaded) == 1


# --- tabla y torneos ------------------------------------------------------

def test_tournament_boundaries():
    df = pd.DataFrame([match("2026-05-20", "A", "B", 1, 0), match("2026-08-01", "A", "B", 0, 0)])
    assert len(current_tournament(df)) == 1
    assert tournament_name(df) == "Apertura 2026"
    assert tournament_name(df.iloc[:1]) == "Clausura 2026"


def test_standings_order_points_then_goal_difference():
    df = pd.DataFrame([
        match("2026-08-01", "A", "C", 3, 0),   # A: +3
        match("2026-08-02", "B", "D", 1, 0),   # B: +1
        match("2026-08-03", "C", "D", 1, 1),
    ])
    table = standings(df)
    assert table["Equipo"].tolist() == ["A", "B", "D", "C"]   # D (-1) arriba de C (-3)
    assert table.loc[1, "Pts"] == 3


def test_standings_ignores_liguilla():
    regular = [match("2026-08-01", "A", "B", 0, 1)] * REGULAR_SEASON_MATCHES
    liguilla = [match("2026-12-01", "A", "B", 9, 0)]
    table = standings(pd.DataFrame(regular + liguilla)).set_index("Equipo")
    assert table.loc["A", "PJ"] == REGULAR_SEASON_MATCHES
    assert table.loc["A", "GF"] == 0


def test_recent_window_keeps_only_last_years():
    df = pd.DataFrame([match("2023-01-01", "A", "B", 1, 0), match("2026-01-01", "A", "B", 1, 0)])
    assert len(recent_window(df, 2)) == 1
    assert len(recent_window(df, None)) == 2


# --- liguilla --------------------------------------------------------------

def rigged_model(matrix_for):
    """Modelo de mentira: matrix_for(home, away) define el marcador de cada partido."""
    size = 3

    def score_matrix(home, away):
        matrix = np.zeros((size, size))
        matrix[matrix_for(home, away)] = 1.0
        return matrix

    return SimpleNamespace(
        poisson_model=SimpleNamespace(score_matrix=score_matrix, max_goals=size - 1),
        check_teams=lambda *teams: None,
    )


def sampler_for(matrix_for, seed=0):
    return _LegSampler(rigged_model(matrix_for), np.random.default_rng(seed))


def test_tied_aggregate_advances_better_seed_not_away_goals():
    """Global 1-1 con gol de visitante del peor sembrado: aun así pasa el mejor."""
    legs = {("Peor", "Mejor"): (0, 0), ("Mejor", "Peor"): (1, 1)}
    assert simulate_series(sampler_for(lambda h, a: legs[(h, a)]), "Mejor", "Peor") == "Mejor"


def test_aggregate_winner_advances_even_if_worse_seed():
    legs = {("Peor", "Mejor"): (2, 0), ("Mejor", "Peor"): (1, 0)}
    assert simulate_series(sampler_for(lambda h, a: legs[(h, a)]), "Mejor", "Peor") == "Peor"


def test_tied_final_can_go_either_way():
    sampler = sampler_for(lambda h, a: (1, 1))
    winners = {simulate_series(sampler, "Mejor", "Peor", is_final=True) for _ in range(50)}
    assert winners == {"Mejor", "Peor"}


def test_semifinals_are_reseeded():
    """Avanzan 1, 7, 3 y 5. Al reacomodar: 1 vs 7 y 3 vs 5.
    Un cuadro fijo daría 1 vs 5 y 3 vs 7."""
    seeds = [f"S{i}" for i in range(1, 9)]
    strength = {team: i for i, team in enumerate(["S1", "S3", "S5", "S7", "S2", "S4", "S6", "S8"])}
    played = set()

    def matrix_for(home, away):
        played.add(frozenset((home, away)))
        return (2, 0) if strength[home] < strength[away] else (0, 2)

    simulate_liguilla(rigged_model(matrix_for), seeds, n_simulations=1, seed=1)

    assert frozenset(("S1", "S7")) in played
    assert frozenset(("S3", "S5")) in played
    assert frozenset(("S1", "S5")) not in played
    assert frozenset(("S3", "S7")) not in played


def test_liguilla_probabilities_sum_to_one():
    teams = [f"T{i}" for i in range(8)]
    rows = [
        match(f"2026-08-{(i % 27) + 1:02d}", teams[i % 8], teams[(i + 1 + i // 8) % 8], i % 3, (i + 1) % 2)
        for i in range(120)
        if teams[i % 8] != teams[(i + 1 + i // 8) % 8]
    ]
    model = EnsemblePredictor().fit(pd.DataFrame(rows))
    probs = simulate_liguilla(model, teams, n_simulations=300, seed=7)
    assert abs(sum(probs.values()) - 1) < 1e-6


# --- validación de equipos ---------------------------------------------------

def fitted_model():
    return EnsemblePredictor().fit(pd.DataFrame([
        match("2026-08-01", "América", "Chivas", 2, 1),
        match("2026-08-08", "Chivas", "América", 0, 0),
    ]))


def test_predict_rejects_unknown_team_and_suggests_name():
    with pytest.raises(ValueError, match="¿Quisiste decir 'América'?"):
        fitted_model().predict("America", "Chivas")


def test_rejected_team_does_not_pollute_ratings():
    """ratings es un defaultdict: leer un nombre nuevo lo crearía."""
    model = fitted_model()
    with pytest.raises(ValueError):
        model.predict("Chivas", "Nadie FC")
    assert "Nadie FC" not in model.elo_model.ratings


def test_liguilla_rejects_unknown_team():
    with pytest.raises(ValueError, match="Equipo desconocido"):
        simulate_liguilla(fitted_model(), ["Nadie FC"] * 8, n_simulations=1)


# --- backtest ---------------------------------------------------------------

def test_backtest_reports_market_benchmark():
    teams = ["A", "B", "C", "D"]
    rows = []
    for year in (2024, 2025):
        for month in range(1, 13):
            for i, home in enumerate(teams):
                rows.append({
                    **match(f"{year}-{month:02d}-15", home, teams[(i + 1) % 4], i % 3, month % 2),
                    "odds_home": 2.0, "odds_draw": 3.5, "odds_away": 4.0,
                })
    result = walk_forward_backtest(pd.DataFrame(rows), start_year=2025)
    assert "market" in result.summary().index
    assert abs(sum(result.records[0]["market"].values()) - 1) < 1e-9


def test_league_config_points_to_liga_mx():
    assert LIGA_MX.name == "Liga MX"
    assert LIGA_MX.date_format == "%d/%m/%Y"
