"""
Simulador de la liguilla de Liga MX (cuartos, semis y final a ida y vuelta).

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
Elo no predice marcadores y la serie se define por el global.
"""

import numpy as np

from src.ensemble import EnsemblePredictor
from src.utils import LIGUILLA_TEAMS


class _LegSampler:
    """Muestrea marcadores de un partido. Guarda la matriz de cada cruce: en
    una liguilla solo hay unas decenas de cruces posibles y recalcularla en
    cada simulación domina el tiempo de ejecución."""

    def __init__(self, model: EnsemblePredictor, rng: np.random.Generator):
        self.model = model
        self.rng = rng
        self._probs: dict[tuple[str, str], np.ndarray] = {}

    def sample(self, home: str, away: str) -> tuple[int, int]:
        key = (home, away)
        if key not in self._probs:
            flat = self.model.poisson_model.score_matrix(home, away).flatten()
            self._probs[key] = flat / flat.sum()

        probs = self._probs[key]
        idx = self.rng.choice(len(probs), p=probs)
        size = self.model.poisson_model.max_goals + 1
        home_goals, away_goals = divmod(int(idx), size)
        return home_goals, away_goals


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

    sampler =_LegSampler(model, np.random.default_rng(seed))
    position = {team: i for i, team in enumerate(seeded_teams)}
    champion_counts = {team: 0 for team in seeded_teams}

    for _ in range(n_simulations):
        semifinalists = [
            simulate_series(sampler, seeded_teams[i], seeded_teams[LIGUILLA_TEAMS - 1 - i])
            for i in range(LIGUILLA_TEAMS // 2)
        ]

        a, b, c, d = sorted(semifinalists, key=position.get)
        finalist_1 = simulate_series(sampler, a, d)
        finalist_2 = simulate_series(sampler, b, c)

        better, worse = sorted([finalist_1, finalist_2], key=position.get)
        champion_counts[simulate_series(sampler, better, worse, is_final=True)] += 1

    return {team: round(count / n_simulations, 4) for team, count in champion_counts.items()}


if __name__ == "__main__":
    from src.data_loader import load_processed
    from src.league_config import LIGA_MX
    from src.utils import current_tournament, standings, tournament_name

    matches = load_processed(LIGA_MX)
    model = EnsemblePredictor(league=LIGA_MX).fit(matches)

    tournament = current_tournament(matches)
    top8 = standings(tournament)["Equipo"].head(LIGUILLA_TEAMS).tolist()
    probs = simulate_liguilla(model, top8, n_simulations=5000)

    print(f"Probabilidad de ser campeón, con el top 8 actual de {tournament_name(tournament)}:")
    for team, p in sorted(probs.items(), key=lambda x: -x[1]):
        print(f"  {team}: {p:.1%}")
