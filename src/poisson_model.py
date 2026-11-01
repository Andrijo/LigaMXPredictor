"""
poisson_model.py
-----------------
Day 2: Modelo de goles Dixon-Coles (1997) para simular marcadores exactos.

Cada equipo tiene una fuerza de ataque y una de defensa, y los goles esperados
de un partido salen de combinarlas:

    log(goles local)     = base + localía + ataque_local + defensa_visitante
    log(goles visitante) = base + ataque_visitante + defensa_local

Todo se ajusta a la vez por máxima verosimilitud, así que meterle dos goles a
Cruz Azul cuenta más que meterle dos a FC Juárez. Dos añadidos sobre eso:

  - Decaimiento temporal: el peso de un partido se reduce a la mitad cada
    half_life_days días.
  - Regularización (ridge): acerca las fuerzas al promedio de la liga para que
    un equipo con pocos partidos no quede con valores extremos.

Además incluye la corrección de Dixon-Coles: el Poisson "puro" asume que los
goles de local y visitante son independientes, pero los marcadores bajos
(0-0, 1-0, 0-1, 1-1) están correlacionados de forma que el modelo puro los
sub/sobre-estima sistemáticamente. Esas 4 celdas se corrigen con un factor
tau(rho), también ajustado por máxima verosimilitud.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import poisson


class PoissonGoalModel:
    def __init__(
        self,
        max_goals: int = 6,
        rho: float = 0.0,
        half_life_days: float | None = None,
        ridge: float = 1.0,
    ):
        self.max_goals = max_goals
        self.rho = rho  # 0.0 = sin corrección Dixon-Coles (Poisson puro)
        self.half_life_days = half_life_days  # None = todos los partidos pesan igual
        self.ridge = ridge
        self.base = 0.0
        self.home_advantage = 0.0
        # En escala logarítmica: 0 = equipo promedio. Mayor ataque = mete más
        # goles; mayor defensa = recibe más goles.
        self.team_attack: dict[str, float] = {}
        self.team_defense: dict[str, float] = {}

    def _match_weights(self, matches: pd.DataFrame, as_of: pd.Timestamp | None) -> np.ndarray:
        if self.half_life_days is None:
            return np.ones(len(matches))
        as_of = matches["date"].max() if as_of is None else as_of
        age_days = (as_of - matches["date"]).dt.days.to_numpy(dtype=float)
        return 0.5 ** (age_days / self.half_life_days)

    def fit(self, matches: pd.DataFrame, fit_rho: bool = True, as_of: pd.Timestamp | None = None):
        """Ajusta los parámetros por máxima verosimilitud con el gradiente
        analítico, lo que mantiene el ajuste en fracciones de segundo.
        as_of: fecha contra la que se mide la antigüedad de los partidos (por
        defecto, el último partido). Si fit_rho=True (default), también ajusta
        el parámetro Dixon-Coles rho."""
        teams = sorted(set(matches["home_team"]) | set(matches["away_team"]))
        team_index = {team: i for i, team in enumerate(teams)}
        n = len(teams)

        home = matches["home_team"].map(team_index).to_numpy()
        away = matches["away_team"].map(team_index).to_numpy()
        home_goals = matches["home_score"].to_numpy(dtype=float)
        away_goals = matches["away_score"].to_numpy(dtype=float)
        weights = self._match_weights(matches, as_of)
        ridge = self.ridge

        def objective(params: np.ndarray) -> tuple[float, np.ndarray]:
            base, home_adv = params[0], params[1]
            attack, defense = params[2:2 + n], params[2 + n:]

            log_home = base + home_adv + attack[home] + defense[away]
            log_away = base + attack[away] + defense[home]
            exp_home, exp_away = np.exp(log_home), np.exp(log_away)

            log_likelihood = (weights * (
                home_goals * log_home - exp_home + away_goals * log_away - exp_away
            )).sum()
            penalty = 0.5 * ridge * ((attack ** 2).sum() + (defense ** 2).sum())

            home_residual = weights * (home_goals - exp_home)
            away_residual = weights * (away_goals - exp_away)
            grad = np.zeros_like(params)
            grad[0] = -(home_residual.sum() + away_residual.sum())
            grad[1] = -home_residual.sum()
            grad[2:2 + n] = ridge * attack - (
                np.bincount(home, home_residual, n) + np.bincount(away, away_residual, n)
            )
            grad[2 + n:] = ridge * defense - (
                np.bincount(away, home_residual, n) + np.bincount(home, away_residual, n)
            )
            return penalty - log_likelihood, grad

        start = np.zeros(2 + 2 * n)
        start[0] = np.log(max(np.average(away_goals, weights=weights), 0.1))
        start[1] = 0.25
        params = minimize(objective, start, jac=True, method="L-BFGS-B").x

        self.base = float(params[0])
        self.home_advantage = float(params[1])
        self.team_attack = dict(zip(teams, params[2:2 + n].tolist()))
        self.team_defense = dict(zip(teams, params[2 + n:].tolist()))

        if fit_rho:
            self.fit_rho(matches, as_of=as_of)

        return self

    @staticmethod
    def _dixon_coles_tau(x: int, y: int, lam: float, mu: float, rho: float) -> float:
        """Factor de corrección de Dixon-Coles para las 4 celdas de marcador bajo.
        Para cualquier otro marcador, tau = 1 (sin corrección)."""
        if x == 0 and y == 0:
            return 1 - lam * mu * rho
        elif x == 0 and y == 1:
            return 1 + lam * rho
        elif x == 1 and y == 0:
            return 1 + mu * rho
        elif x == 1 and y == 1:
            return 1 - rho
        return 1.0

    def fit_rho(self, matches: pd.DataFrame, as_of: pd.Timestamp | None = None) -> float:
        """
        Ajusta rho por máxima verosimilitud. Como tau=1 fuera de las 4 celdas
        de marcador bajo, la log-verosimilitud solo depende de rho a través de
        esos partidos — filtramos a ellos y optimizamos de forma vectorizada.
        """
        attack = matches["home_team"].map(self.team_attack).to_numpy()
        defense = matches["home_team"].map(self.team_defense).to_numpy()
        away_attack = matches["away_team"].map(self.team_attack).to_numpy()
        away_defense = matches["away_team"].map(self.team_defense).to_numpy()

        lam = np.exp(self.base + self.home_advantage + attack + away_defense)
        mu = np.exp(self.base + away_attack + defense)

        x = matches["home_score"].to_numpy()
        y = matches["away_score"].to_numpy()
        weights = self._match_weights(matches, as_of)

        mask = (x <= 1) & (y <= 1)
        lam_m, mu_m, x_m, y_m, w_m = lam[mask], mu[mask], x[mask], y[mask], weights[mask]

        if len(lam_m) == 0:
            self.rho = 0.0
            return self.rho

        idx00 = (x_m == 0) & (y_m == 0)
        idx01 = (x_m == 0) & (y_m == 1)
        idx10 = (x_m == 1) & (y_m == 0)
        idx11 = (x_m == 1) & (y_m == 1)

        def neg_log_likelihood(rho: float) -> float:
            tau = np.ones_like(lam_m)
            tau[idx00] = 1 - lam_m[idx00] * mu_m[idx00] * rho
            tau[idx01] = 1 + lam_m[idx01] * rho
            tau[idx10] = 1 + mu_m[idx10] * rho
            tau[idx11] = 1 - rho
            tau = np.clip(tau, 1e-6, None)  # tau debe ser > 0 para poder sacar log
            return -np.sum(w_m * np.log(tau))

        result = minimize_scalar(neg_log_likelihood, bounds=(-0.3, 0.3), method="bounded")
        self.rho = float(result.x)
        return self.rho

    def expected_goals(self, home_team: str, away_team: str) -> tuple[float, float]:
        """Goles esperados. Un equipo sin partidos en el entrenamiento cuenta como promedio."""
        home_attack = self.team_attack.get(home_team, 0.0)
        home_defense = self.team_defense.get(home_team, 0.0)
        away_attack = self.team_attack.get(away_team, 0.0)
        away_defense = self.team_defense.get(away_team, 0.0)

        exp_home_goals = np.exp(self.base + self.home_advantage + home_attack + away_defense)
        exp_away_goals = np.exp(self.base + away_attack + home_defense)

        return float(exp_home_goals), float(exp_away_goals)

    def score_matrix(self, home_team: str, away_team: str) -> np.ndarray:
        """Matriz de probabilidad para cada marcador posible (home_goals x away_goals),
        con la corrección Dixon-Coles aplicada a las 4 celdas de marcador bajo si rho != 0."""
        exp_home, exp_away = self.expected_goals(home_team, away_team)

        goals = np.arange(self.max_goals + 1)
        matrix = np.outer(poisson.pmf(goals, exp_home), poisson.pmf(goals, exp_away))

        if self.rho != 0.0:
            for x, y in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                matrix[x, y] *= self._dixon_coles_tau(x, y, exp_home, exp_away, self.rho)

        # La corrección redistribuye masa y la matriz corta en max_goals
        return matrix / matrix.sum()

    def top_scores(self, home_team: str, away_team: str, n: int = 3) -> list[tuple[str, float]]:
        """Devuelve los n marcadores más probables como [('1-1', 0.14), ('1-0', 0.11), ...].
        Más informativo que un solo 'marcador más probable': con goles esperados
        bajos (típico en fútbol), la moda de Poisson concentra mucha masa en 1-1
        aunque un equipo sea claramente favorito, así que un solo marcador
        aislado puede ser engañoso sobre quién es favorito."""
        matrix = self.score_matrix(home_team, away_team)
        flat_indices = np.argsort(matrix.ravel())[::-1][:n]
        scores = []
        for idx in flat_indices:
            h, a = np.unravel_index(idx, matrix.shape)
            scores.append((f"{h}-{a}", round(float(matrix[h, a]), 4)))
        return scores

    def predict(self, home_team: str, away_team: str) -> dict:
        """Probabilidades 1X2, marcador más probable y top-3 de marcadores."""
        matrix = self.score_matrix(home_team, away_team)

        p_home_win = np.tril(matrix, -1).sum()
        p_draw = np.trace(matrix)
        p_away_win = np.triu(matrix, 1).sum()

        most_likely_idx = np.unravel_index(matrix.argmax(), matrix.shape)
        top_scores = self.top_scores(home_team, away_team, n=3)

        return {
            "home_win": round(float(p_home_win), 4),
            "draw": round(float(p_draw), 4),
            "away_win": round(float(p_away_win), 4),
            "most_likely_score": f"{most_likely_idx[0]}-{most_likely_idx[1]}",
            "top_scores": top_scores,
        }


if __name__ == "__main__":
    from src.data_loader import load_processed
    from src.league_config import LIGA_MX

    matches = load_processed()
    model = PoissonGoalModel(
        half_life_days=LIGA_MX.poisson_half_life_days,
        ridge=LIGA_MX.poisson_ridge,
    ).fit(matches)

    print(f"Rho (Dixon-Coles) ajustado: {model.rho:.4f}")
    print(f"Ventaja de local: {np.exp(model.home_advantage):.2f}x goles")
    print("Predicción América vs Chivas:")
    print(model.predict("América", "Chivas"))
