import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.poisson_model import PoissonGoalModel


def match(date, home, away, home_score, away_score):
    return {
        "date": pd.Timestamp(date), "home_team": home, "away_team": away,
        "home_score": home_score, "away_score": away_score,
    }


def simulated_league(n_rounds=40, seed=0):
    """Liga sintética con fuerzas conocidas para comprobar que el ajuste las recupera."""
    rng = np.random.default_rng(seed)
    attack = {"Fuerte": 0.4, "Medio": 0.0, "Debil": -0.4}
    defense = {"Fuerte": -0.3, "Medio": 0.0, "Debil": 0.3}
    rows = []
    date = pd.Timestamp("2025-01-01")
    for _ in range(n_rounds):
        for home in attack:
            for away in attack:
                if home != away:
                    home_goals = rng.poisson(np.exp(0.1 + 0.25 + attack[home] + defense[away]))
                    away_goals = rng.poisson(np.exp(0.1 + attack[away] + defense[home]))
                    rows.append(match(date, home, away, home_goals, away_goals))
                    date += pd.Timedelta(days=1)
    return pd.DataFrame(rows)


def test_recovers_home_advantage_and_team_order():
    model = PoissonGoalModel().fit(simulated_league())
    assert model.home_advantage == pytest.approx(0.25, abs=0.1)
    assert model.team_attack["Fuerte"] > model.team_attack["Medio"] > model.team_attack["Debil"]
    assert model.team_defense["Fuerte"] < model.team_defense["Medio"] < model.team_defense["Debil"]


def test_goals_are_adjusted_for_opponent_strength():
    """A y B meten lo mismo, pero A lo hace contra un rival que casi no recibe goles."""
    rows = []
    date = pd.Timestamp("2025-01-01")
    for _ in range(30):
        rows.append(match(date, "A", "Muralla", 1, 0))
        rows.append(match(date, "Muralla", "A", 0, 1))
        rows.append(match(date, "B", "Coladera", 1, 0))
        rows.append(match(date, "Coladera", "B", 0, 1))
        rows.append(match(date, "Muralla", "Coladera", 3, 0))
        rows.append(match(date, "Coladera", "Muralla", 0, 3))
        date += pd.Timedelta(days=7)

    model = PoissonGoalModel(ridge=0.1).fit(pd.DataFrame(rows), fit_rho=False)
    assert model.team_attack["A"] > model.team_attack["B"]


def test_recent_matches_weigh_more_with_half_life():
    """X fue goleador hace años y ahora no mete goles; con decaimiento debe pesar lo reciente."""
    rows = []
    for year, scored in ((2020, 4), (2026, 0)):
        for month in range(1, 13):
            rows.append(match(f"{year}-{month:02d}-10", "X", "Y", scored, 1))
            rows.append(match(f"{year}-{month:02d}-20", "Y", "X", 1, scored))
    df = pd.DataFrame(rows)

    equal = PoissonGoalModel().fit(df, fit_rho=False)
    decayed = PoissonGoalModel(half_life_days=180).fit(df, fit_rho=False)
    assert decayed.team_attack["X"] < equal.team_attack["X"]


def test_as_of_changes_match_weights():
    df = pd.DataFrame([match("2026-01-01", "A", "B", 1, 0), match("2026-07-01", "A", "B", 1, 0)])
    weights = PoissonGoalModel(half_life_days=181)._match_weights(df, pd.Timestamp("2026-07-01"))
    assert weights[0] == pytest.approx(0.5)
    assert weights[1] == pytest.approx(1.0)


def test_unknown_team_counts_as_average():
    model = PoissonGoalModel().fit(simulated_league())
    assert model.expected_goals("Nuevo", "Otro") == pytest.approx(
        (np.exp(model.base + model.home_advantage), np.exp(model.base))
    )


def test_score_matrix_is_a_probability_distribution():
    model = PoissonGoalModel().fit(simulated_league())
    matrix = model.score_matrix("Fuerte", "Debil")
    assert matrix.sum() == pytest.approx(1.0)
    assert (matrix >= 0).all()


def test_predict_probabilities_sum_to_one():
    result = PoissonGoalModel().fit(simulated_league()).predict("Medio", "Debil")
    assert sum(result[k] for k in ("home_win", "draw", "away_win")) == pytest.approx(1.0, abs=1e-3)


def test_home_team_is_favored_in_even_match():
    result = PoissonGoalModel().fit(simulated_league()).predict("Medio", "Medio")
    assert result["home_win"] > result["away_win"]
