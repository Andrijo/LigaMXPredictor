"""
Simulador de la liguilla de Liga MX (cuartos, semis y final a ida y vuelta) y
del torneo completo a partir de lo que falta de la fase regular.

Reglas que simula (formato vigente, sin Play-In):
  - Clasifican directo los 8 primeros de la tabla general.
  - Cuartos: 1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5.
  - Semis: se reacomoda el cuadro, el mejor sembrado que sigue vivo enfrenta
    al peor, y los otros dos entre sí.
  - El mejor sembrado de cada serie cierra en casa.
  - Empate en el global: en cuartos y semis avanza el mejor sembrado; en la
    final hay tiempos extra y penales (aproximados con 50/50). No existe el
    gol de visitante.

Usa la matriz de marcadores del modelo Poisson del EnsemblePredictor, porque
Elo no predice marcadores y tanto la tabla como las series dependen de ellos.
"""

import numpy as np
import pandas as pd

from src.ensemble import EnsemblePredictor
from src.utils import LIGUILLA_TEAMS, standings


class _LegSampler:
    """Muestrea marcadores de un partido. Guarda la matriz de cada cruce: en
    una liguilla solo hay unas decenas de cruces posibles y recalcularla en
    cada simulación domina el tiempo de ejecución."""

    def __init__(self, model: EnsemblePredictor, rng: np.random.Generator):
        self.model = model
        self.rng = rng
        self.size = model.poisson_model.max_goals + 1
        self._probs: dict[tuple[str, str], np.ndarray] = {}

    def _flat_probs(self, home: str, away: str) -> np.ndarray:
        key = (home, away)
        if key not in self._probs:
            flat = self.model.poisson_model.score_matrix(home, away).flatten()
            self._probs[key] = flat / flat.sum()
        return self._probs[key]

    def sample(self, home: str, away: str) -> tuple[int, int]:
        probs = self._flat_probs(home, away)
        home_goals, away_goals = divmod(int(self.rng.choice(len(probs), p=probs)), self.size)
        return home_goals, away_goals

    def sample_many(self, home: str, away: str, n: int) -> tuple[np.ndarray, np.ndarray]:
        """n marcadores del mismo partido, como dos arreglos (goles local, goles visitante)."""
        probs = self._flat_probs(home, away)
        return np.divmod(self.rng.choice(len(probs), size=n, p=probs), self.size)


def simulate_series(sampler: _LegSampler, better_seed: str, worse_seed: str, is_final: bool = False) -> str:
    """Simula una serie a ida y vuelta y devuelve al equipo que avanza."""
    first_worse, first_better = sampler.sample(worse_seed, better_seed)   # ida en casa del peor sembrado
    second_better, second_worse = sampler.sample(better_seed, worse_seed)  # vuelta en casa del mejor

    global_better = first_better + second_better
    global_worse = first_worse + second_worse

    if global_better != global_worse:
        return better_seed if global_better > global_worse else worse_seed

    if is_final:
        return better_seed if sampler.rng.random() < 0.5 else worse_seed

    return better_seed


def _play_bracket(sampler: _LegSampler, seeded_teams: list[str]) -> str:
    """Juega una liguilla completa y devuelve al campeón."""
    position = {team: i for i, team in enumerate(seeded_teams)}

    semifinalists = [
        simulate_series(sampler, seeded_teams[i], seeded_teams[LIGUILLA_TEAMS - 1 - i])
        for i in range(LIGUILLA_TEAMS // 2)
    ]

    a, b, c, d = sorted(semifinalists, key=position.get)
    finalist_1 = simulate_series(sampler, a, d)
    finalist_2 = simulate_series(sampler, b, c)

    better, worse = sorted([finalist_1, finalist_2], key=position.get)
    return simulate_series(sampler, better, worse, is_final=True)


def simulate_liguilla(
    model: EnsemblePredictor,
    seeded_teams: list[str],
    n_simulations: int = 1000,
    seed: int | None = None,
) -> dict:
    """
    seeded_teams: los 8 clasificados en orden de la tabla (1° a 8°).
    Devuelve la probabilidad de ser campeón de cada equipo.
    """
    assert len(seeded_teams) == LIGUILLA_TEAMS, "La liguilla de Liga MX se juega con 8 equipos"
    model.check_teams(*seeded_teams)

    sampler = _LegSampler(model, np.random.default_rng(seed))
    champion_counts = {team: 0 for team in seeded_teams}

    for _ in range(n_simulations):
        champion_counts[_play_bracket(sampler, seeded_teams)] += 1

    return {team: round(count / n_simulations, 4) for team, count in champion_counts.items()}


def simulate_tournament(
    model: EnsemblePredictor,
    tournament: pd.DataFrame,
    scheduled: pd.DataFrame,
    n_simulations: int = 2000,
    seed: int | None = None,
) -> pd.DataFrame:
    """
    Simula lo que falta de la fase regular y luego la liguilla que resulte de
    cada tabla final, para que la incertidumbre de la clasificación y de la
    siembra llegue hasta el campeón.

    tournament: partidos ya jugados del torneo.
    scheduled: partidos por jugarse, con localía conocida.
    """
    table = standings(tournament)
    teams = table["Equipo"].tolist()
    model.check_teams(*teams)
    index = {team: i for i, team in enumerate(teams)}

    points = np.tile(table["Pts"].to_numpy(dtype=float), (n_simulations, 1))
    goal_diff = np.tile(table["DG"].to_numpy(dtype=float), (n_simulations, 1))
    goals_for = np.tile(table["GF"].to_numpy(dtype=float), (n_simulations, 1))

    rng = np.random.default_rng(seed)
    sampler = _LegSampler(model, rng)

    for home, away in zip(scheduled["home_team"], scheduled["away_team"]):
        i, j = index[home], index[away]
        home_goals, away_goals = sampler.sample_many(home, away, n_simulations)
        points[:, i] += 3 * (home_goals > away_goals) + (home_goals == away_goals)
        points[:, j] += 3 * (away_goals > home_goals) + (home_goals == away_goals)
        goal_diff[:, i] += home_goals - away_goals
        goal_diff[:, j] += away_goals - home_goals
        goals_for[:, i] += home_goals
        goals_for[:, j] += away_goals

    # Orden de la tabla: puntos, diferencia de goles, goles a favor. Un empate
    # en los tres se rompe al azar porque no modelamos los demás criterios.
    sort_key = points * 1e6 + (goal_diff + 500) * 1e3 + goals_for + rng.random(points.shape)
    final_order = np.argsort(-sort_key, axis=1)

    qualified = np.zeros(len(teams))
    champions = np.zeros(len(teams))
    for order in final_order:
        top8 = order[:LIGUILLA_TEAMS]
        qualified[top8] += 1
        champions[index[_play_bracket(sampler, [teams[i] for i in top8])]] += 1

    result = pd.DataFrame({
        "Equipo": teams,
        "Pts": table["Pts"].to_numpy(),
        "Pts esperados": points.mean(axis=0).round(1),
        "Clasifica": (qualified / n_simulations).round(4),
        "Campeón": (champions / n_simulations).round(4),
    })
    return result.sort_values(["Campeón", "Clasifica"], ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    from src.data_loader import load_processed
    from src.fixtures import (
        load_fixtures,
        missing_fixtures,
        scheduled_fixtures,
        with_played_fixtures,
    )
    from src.league_config import LIGA_MX
    from src.utils import current_tournament, tournament_name

    pd.set_option("display.width", 120)

    matches = load_processed(LIGA_MX)
    model = EnsemblePredictor(league=LIGA_MX).fit(matches)

    tournament = current_tournament(matches)
    fixtures = load_fixtures(tournament)
    scheduled = scheduled_fixtures(fixtures)
    missing = missing_fixtures(tournament, fixtures)

    if scheduled.empty or missing:
        reason = f"faltan {missing} partidos en el calendario" if missing else "no quedan partidos por jugar"
        top8 = standings(with_played_fixtures(tournament, fixtures))["Equipo"].head(LIGUILLA_TEAMS).tolist()
        print(f"Liguilla con el top 8 actual de {tournament_name(tournament)} ({reason}):")
        for team, p in sorted(simulate_liguilla(model, top8, n_simulations=5000).items(), key=lambda x: -x[1]):
            print(f"  {team}: {p:.1%}")
    else:
        print(f"Proyección de {tournament_name(tournament)}, faltan {len(scheduled)} partidos:")
        print(simulate_tournament(model, with_played_fixtures(tournament, fixtures), scheduled, 5000).to_string())
