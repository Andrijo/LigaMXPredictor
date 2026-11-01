"""
Configuración de Liga MX: fuente de datos, nombres de equipos y parámetros
del modelo (ventaja de local, altitud).
"""

from dataclasses import dataclass, field


# football-data.co.uk publica el histórico de Liga MX desde 2012/13 en un solo
# CSV y lo actualiza durante la temporada (Apertura y Clausura + liguilla).
LIGA_MX_DATA_URL = "https://www.football-data.co.uk/new/MEX.csv"

# Nombre en la fuente -> nombre que usa todo el proyecto.
# Normalizamos aquí, al cargar, para que el resto del código y el dashboard
# solo vean un nombre por equipo.
TEAM_NAMES = {
    "Atl. San Luis": "Atlético San Luis",
    "Club America": "América",
    "Club Leon": "León",
    "Club Tijuana": "Tijuana",
    "Guadalajara Chivas": "Chivas",
    "Juarez": "FC Juárez",
    "Mazatlan FC": "Mazatlán",
    "Monarcas": "Morelia",
    "Queretaro": "Querétaro",
    "Santos Laguna": "Santos",
    "Tigres UANL": "Tigres",
    "UNAM Pumas": "Pumas",
}

# Altitud aproximada (metros sobre el nivel del mar) de las sedes de equipos
# que juegan en altitud significativa. Se usa como bonus extra de local, más
# allá del home_advantage genérico. Las claves deben ser nombres normalizados
# (ver TEAM_NAMES); tests/test_liga_mx.py verifica que no queden huérfanas.
LIGA_MX_ALTITUDE_TEAMS = {
    "Toluca": 2680,
    "Cruz Azul": 2240,    # CDMX
    "América": 2240,      # CDMX
    "Pumas": 2240,        # CDMX
    "Atlante": 2240,      # CDMX desde su regreso en Apertura 2026
    "Pachuca": 2426,
    "León": 1815,
    "Atlas": 1566,        # Guadalajara
    "Chivas": 1566,       # Guadalajara
}


@dataclass
class LeagueConfig:
    name: str
    data_source: str
    date_col: str = "date"
    date_format: str = "%Y-%m-%d"
    home_team_col: str = "home_team"
    away_team_col: str = "away_team"
    home_score_col: str = "home_score"
    away_score_col: str = "away_score"
    home_advantage: float = 60       # bonus base de Elo por jugar de local
    altitude_teams: dict = field(default_factory=dict)  # equipo -> metros
    altitude_bonus_per_1000m: float = 25  # puntos Elo extra por cada 1000m de altitud
    poisson_window_years: int | None = None  # años recientes para el Poisson (None = todos)


LIGA_MX = LeagueConfig(
    name="Liga MX",
    data_source=LIGA_MX_DATA_URL,
    date_col="Date",
    date_format="%d/%m/%Y",          # ojo: día primero (02/07/2022 = 2 de julio)
    home_team_col="Home",
    away_team_col="Away",
    home_score_col="HG",
    away_score_col="AG",
    # Calibrados con backtest walk-forward 2018-2026 (ver README). El bonus de
    # altitud queda en 0 porque empeoraba Elo: esa ventaja ya está dentro del
    # rating de cada equipo y del home_advantage. Súbelo para volver a probarlo.
    home_advantage=60,
    altitude_teams=LIGA_MX_ALTITUDE_TEAMS,
    altitude_bonus_per_1000m=0,
    # Con planteles que rotan cada torneo, lo que hizo un equipo hace más de
    # dos años dice poco de su fuerza actual.
    poisson_window_years=2,
)
