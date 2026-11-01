"""
backtest.py
-----------
Validación walk-forward (fuera de muestra) del ensemble Elo + Poisson.

Por qué hace falta: sin esto, no hay forma de saber si el modelo predice
bien o si un cambio (ej. Dixon-Coles, pesos del ensemble) mejora o empeora
las predicciones. Es la vara de medir para todo lo demás.

Cómo funciona (walk-forward por año):
  Para cada trimestre T desde --start-year hasta el último con datos:
    1. Se entrena solo con lo anterior a T (nunca datos futuros -> sin fuga
       de información)
    2. Se predice cada partido de T
    3. Se compara la predicción contra el resultado real
    4. El Elo se actualiza partido a partido según se avanza (aprendizaje
       online real); el Poisson se reentrena cada trimestre (es un modelo
       por lotes, reentrenarlo partido a partido sería demasiado costoso y
       no cambia la conclusión de forma material)

Métricas:
  - Log-loss: penaliza fuerte estar muy seguro y equivocado (más bajo = mejor)
  - Brier score: error cuadrático medio sobre las 3 probabilidades (más bajo = mejor)
  - Accuracy: aciertos del resultado más probable (1X2)
  - Baseline ingenuo: probabilidades fijas = frecuencia histórica de
    home_win/draw/away_win en el set de entrenamiento inicial. Si el modelo
    no le gana a esto, no está aportando nada.
  - Mercado: probabilidades implícitas en el momio promedio de cierre, sin el
    margen de las casas. Es la referencia difícil: ganarle en log-loss de
    forma sostenida es muy raro.
"""

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.elo import EloModel
from src.poisson_model import PoissonGoalModel
from src.league_config import LeagueConfig, LIGA_MX
from src.utils import recent_window

OUTCOMES = ("home_win", "draw", "away_win")


def _actual_outcome(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "home_win"
    if home_score < away_score:
        return "away_win"
    return "draw"


def _combine(elo_pred: dict, poisson_pred: dict, elo_weight: float, poisson_weight: float) -> dict:
    return {k: elo_weight * elo_pred[k] + poisson_weight * poisson_pred[k] for k in OUTCOMES}


def _market_probs(odds_home: float, odds_draw: float, odds_away: float) -> dict | None:
    """Probabilidades implícitas en los momios, normalizadas para quitar el
    margen de la casa. None si al partido le faltan momios."""
    inverse = [1 / odds for odds in (odds_home, odds_draw, odds_away)]
    if any(math.isnan(p) for p in inverse):
        return None
    total = sum(inverse)
    return {k: p / total for k, p in zip(OUTCOMES, inverse)}


@dataclass
class BacktestResult:
    records: list = field(default_factory=list)  # cada uno: {elo, poisson, ensemble, naive, market, actual, date, ...}

    def _usable(self) -> list:
        """Partidos con momios, para comparar todos los modelos sobre los
        mismos partidos aunque a alguno le falte el mercado."""
        return [r for r in self.records if r["market"] is not None]

    def log_loss(self, key: str) -> float:
        eps = 1e-15
        records = self._usable()
        total = 0.0
        for r in records:
            p = max(r[key][r["actual"]], eps)
            total += -math.log(p)
        return total / len(records)

    def brier_score(self, key: str) -> float:
        records = self._usable()
        total = 0.0
        for r in records:
            p = r[key]
            for outcome in OUTCOMES:
                actual = 1.0 if outcome == r["actual"] else 0.0
                total += (p[outcome] - actual) ** 2
        return total / len(records)

    def accuracy(self, key: str) -> float:
        records = self._usable()
        correct = sum(
            1 for r in records
            if max(OUTCOMES, key=lambda o: r[key][o]) == r["actual"]
        )
        return correct / len(records)

    def summary(self, keys: tuple[str, ...] = ("naive", "elo", "poisson", "ensemble", "market")) -> pd.DataFrame:
        rows = []
        for key in keys:
            rows.append({
                "modelo": key,
                "log_loss": round(self.log_loss(key), 4),
                "brier_score": round(self.brier_score(key), 4),
                "accuracy": round(self.accuracy(key), 4),
            })
        return pd.DataFrame(rows).set_index("modelo")


def walk_forward_backtest(
    matches: pd.DataFrame,
    start_year: int,
    end_year: int | None = None,
    elo_weight: float = 0.5,
    poisson_weight: float = 0.5,
    league: LeagueConfig = LIGA_MX,
    fit_rho: bool = True,
) -> BacktestResult:
    """
    Corre la validación walk-forward y devuelve un BacktestResult con las
    predicciones (elo, poisson, ensemble, naive, market) y el resultado real
    de cada partido, listo para calcular métricas con .summary().
    """
    matches = matches.sort_values("date").reset_index(drop=True)
    if end_year is None:
        end_year = int(matches["date"].dt.year.max())

    initial_train = matches[matches["date"].dt.year < start_year]
    if initial_train.empty:
        raise ValueError(
            f"No hay partidos antes de {start_year} para entrenar. "
            f"Elige un start_year posterior al primer año del dataset."
        )

    # Baseline ingenuo: frecuencia histórica de cada resultado, fija para
    # todos los partidos de test (no se actualiza durante el backtest).
    naive_outcomes = initial_train.apply(
        lambda r: _actual_outcome(r["home_score"], r["away_score"]), axis=1
    )
    naive_freqs = naive_outcomes.value_counts(normalize=True)
    naive_probs = {k: float(naive_freqs.get(k, 0.0)) for k in OUTCOMES}

    elo_model = EloModel(
        home_advantage=league.home_advantage,
        altitude_teams=league.altitude_teams,
        altitude_bonus_per_1000m=league.altitude_bonus_per_1000m,
    )
    elo_model.fit(initial_train)

    result = BacktestResult()

    test_matches = matches[matches["date"].dt.year.between(start_year, end_year)]

    for quarter, test_df in test_matches.groupby(test_matches["date"].dt.to_period("Q")):
        cutoff = quarter.start_time
        train_df = recent_window(matches[matches["date"] < cutoff], league.poisson_window_years, as_of=cutoff)
        poisson_model = PoissonGoalModel().fit(train_df, fit_rho=fit_rho)

        for _, row in test_df.iterrows():
            elo_pred = elo_model.predict(row["home_team"], row["away_team"])
            poisson_pred = poisson_model.predict(row["home_team"], row["away_team"])
            ensemble_pred = _combine(elo_pred, poisson_pred, elo_weight, poisson_weight)
            actual = _actual_outcome(row["home_score"], row["away_score"])

            result.records.append({
                "date": row["date"],
                "home_team": row["home_team"],
                "away_team": row["away_team"],
                "elo": elo_pred,
                "poisson": poisson_pred,
                "ensemble": ensemble_pred,
                "naive": naive_probs,
                "market": _market_probs(row["odds_home"], row["odds_draw"], row["odds_away"]),
                "actual": actual,
            })

            # Elo se actualiza partido a partido según avanza el torneo (online real)
            elo_model.update(row["home_team"], row["away_team"], row["home_score"], row["away_score"])

    if not result.records:
        raise ValueError(f"No hubo partidos de test entre {start_year} y {end_year}.")

    return result


if __name__ == "__main__":
    import argparse
    from src.data_loader import load_processed

    parser = argparse.ArgumentParser(description="Backtesting walk-forward del predictor")
    parser.add_argument("--start-year", type=int, default=2018)
    parser.add_argument("--end-year", type=int, default=None)
    parser.add_argument("--elo-weight", type=float, default=0.5)
    parser.add_argument("--no-dixon-coles", action="store_true", help="Desactiva la corrección Dixon-Coles para comparar")
    args = parser.parse_args()

    matches = load_processed()

    print(f"Backtesting Liga MX: {args.start_year} -> {args.end_year or 'último año disponible'}")
    print(f"Partidos de entrenamiento inicial: {len(matches[matches['date'].dt.year < args.start_year]):,}")
    print()

    result = walk_forward_backtest(
        matches,
        start_year=args.start_year,
        end_year=args.end_year,
        elo_weight=args.elo_weight,
        poisson_weight=1 - args.elo_weight,
        fit_rho=not args.no_dixon_coles,
    )

    print(f"Total de partidos evaluados fuera de muestra: {len(result.records):,}")
    print()
    print(result.summary())
    print()
    print("Más bajo es mejor en log_loss y brier_score. Más alto es mejor en accuracy.")
    print("Si 'naive' gana en alguna métrica, ese modelo no está aportando nada ahí.")
    print("'market' es el momio de cierre: la distancia a él es lo que le falta al modelo.")
