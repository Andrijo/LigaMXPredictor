"""
data_loader.py
--------------
Descarga y limpia el histórico de partidos de Liga MX.

El dataframe de salida queda normalizado a las columnas:
date, season, home_team, away_team, home_score, away_score, result
más los momios promedio de cierre (odds_home, odds_draw, odds_away), que el
backtest usa como referencia del mercado.

Como la liga sigue en curso, los datos locales caducan: load_processed vuelve
a descargarlos si tienen más de MAX_DATA_AGE_HOURS horas.
"""

from pathlib import Path
import time

import pandas as pd
import requests

from src.league_config import LeagueConfig, LIGA_MX, TEAM_NAMES

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
RAW_FILENAME = "liga_mx.csv"
PROCESSED_FILENAME = "liga_mx_clean.csv"
MAX_DATA_AGE_HOURS = 24

ODDS_COLS = {"AvgCH": "odds_home", "AvgCD": "odds_draw", "AvgCA": "odds_away"}


def download_data(url: str, filename: str = RAW_FILENAME) -> Path:
    """Descarga el CSV crudo y lo guarda en data/raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / filename

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    out_path.write_bytes(response.content)

    print(f"Datos descargados en: {out_path}")
    return out_path


def load_raw(league: LeagueConfig = LIGA_MX, refresh: bool = False) -> pd.DataFrame:
    """Carga el CSV crudo desde data/raw/, descargándolo si falta o si refresh=True."""
    path = RAW_DIR / RAW_FILENAME
    if refresh or not path.exists():
        path = download_data(league.data_source)
    return pd.read_csv(path, encoding="utf-8-sig")


def clean_data(df: pd.DataFrame, league: LeagueConfig = LIGA_MX) -> pd.DataFrame:
    """Limpia el CSV crudo y lo normaliza al esquema común del proyecto."""
    df = df.rename(columns={
        league.date_col: "date",
        league.home_team_col: "home_team",
        league.away_team_col: "away_team",
        league.home_score_col: "home_score",
        league.away_score_col: "away_score",
        "Season": "season",
        **ODDS_COLS,
    })

    df["date"] = pd.to_datetime(df["date"], errors="coerce", format=league.date_format)
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")

    # Partidos sin marcador (aún no jugados) se descartan junto con cualquier otro nulo.
    df = df.dropna(subset=["date", "home_team", "away_team", "home_score", "away_score"]).copy()

    df["home_team"] = df["home_team"].str.strip().replace(TEAM_NAMES)
    df["away_team"] = df["away_team"].str.strip().replace(TEAM_NAMES)
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)

    df["result"] = df.apply(
        lambda r: 1 if r["home_score"] > r["away_score"]
        else (-1 if r["home_score"] < r["away_score"] else 0),
        axis=1,
    )

    keep_cols = [
        "date", "season", "home_team", "away_team", "home_score", "away_score", "result",
        *ODDS_COLS.values(),
    ]
    # mergesort: estable, conserva el orden de la fuente dentro de un mismo día
    return df[keep_cols].sort_values("date", kind="mergesort").reset_index(drop=True)


def save_processed(df: pd.DataFrame, filename: str = PROCESSED_FILENAME) -> Path:
    """Guarda el dataframe limpio en data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / filename
    df.to_csv(out_path, index=False)
    print(f"Datos procesados guardados en: {out_path}")
    return out_path


def refresh_data(league: LeagueConfig = LIGA_MX) -> pd.DataFrame:
    """Descarga la versión más reciente y regenera el dataset procesado."""
    clean = clean_data(load_raw(league, refresh=True), league)
    save_processed(clean)
    return clean


def _age_hours(path: Path) -> float:
    return (time.time() - path.stat().st_mtime) / 3600


def load_processed(
    league: LeagueConfig = LIGA_MX,
    max_age_hours: float | None = MAX_DATA_AGE_HOURS,
) -> pd.DataFrame:
    """
    Carga el dataset limpio. Si no existe, o si tiene más de max_age_hours,
    lo actualiza desde la fuente (max_age_hours=None desactiva la caducidad).
    Si la actualización falla pero hay una copia local, sigue con esa copia:
    es mejor predecir con datos de ayer que tumbar el dashboard.
    """
    path = PROCESSED_DIR / PROCESSED_FILENAME

    if not path.exists():
        return refresh_data(league)

    if max_age_hours is not None and _age_hours(path) > max_age_hours:
        try:
            return refresh_data(league)
        except requests.RequestException as exc:
            print(f"No se pudieron actualizar los datos, usando copia local: {exc}")

    return pd.read_csv(path, parse_dates=["date"])


if __name__ == "__main__":
    clean_df = refresh_data()
    print(clean_df.tail())
    print(f"\nTotal de partidos: {len(clean_df):,}")
    print(f"Último partido: {clean_df['date'].max():%Y-%m-%d}")
