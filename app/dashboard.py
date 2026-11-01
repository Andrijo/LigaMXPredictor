"""
dashboard.py
------------
Day 3: Interfaz interactiva en Streamlit para explorar predicciones de
Liga MX con el ensemble Elo + Poisson.

Ejecutar con:
    streamlit run app/dashboard.py
"""

import sys
from pathlib import Path

# Permite importar desde src/ al correr streamlit desde la raíz del proyecto
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_processed
from src.ensemble import EnsemblePredictor
from src.liguilla import simulate_liguilla
from src.model_cache import load_or_fit
from src.utils import (
    LIGUILLA_TEAMS,
    current_tournament,
    get_team_list,
    head_to_head,
    standings,
    tournament_name,
)

st.set_page_config(page_title="Liga MX Predictor", layout="wide")

def _skeleton_box(height: str, width: str = "100%", margin_bottom: str = "12px") -> str:
    """Un bloque gris con animación de brillo (shimmer), imitando la forma
    del contenido real mientras carga. rgba en vez de colores fijos para que
    se vea razonable tanto en tema claro como oscuro de Streamlit."""
    return (
        f'<div style="height:{height};width:{width};margin-bottom:{margin_bottom};'
        f'border-radius:8px;background:linear-gradient(90deg, '
        f'rgba(128,128,128,0.12) 25%, rgba(128,128,128,0.22) 37%, '
        f'rgba(128,128,128,0.12) 63%);background-size:400% 100%;'
        f'animation:skeleton-shimmer 1.4s ease infinite;"></div>'
    )


def show_skeleton():
    """Placeholder de carga que imita la forma del dashboard real:
    subtítulo, dos selectores de equipo, gráfico de barras y 3 métricas."""
    st.markdown(
        "<style>@keyframes skeleton-shimmer "
        "{0%{background-position:200% 0} 100%{background-position:-200% 0}}</style>"
        + _skeleton_box("20px", "40%")
        + '<div style="display:flex;gap:16px;margin:16px 0;">'
        + _skeleton_box("38px", "50%", "0")
        + _skeleton_box("38px", "50%", "0")
        + "</div>"
        + _skeleton_box("260px")
        + '<div style="display:flex;gap:16px;">'
        + _skeleton_box("70px", "33%", "0")
        + _skeleton_box("70px", "33%", "0")
        + _skeleton_box("70px", "33%", "0")
        + "</div>",
        unsafe_allow_html=True,
    )

# ttl: el dataset caduca a las 24 h (ver load_processed); revisar cada hora
# hace que un dashboard que lleva días abierto también tome los datos nuevos.
@st.cache_data(ttl=3600)
def get_matches() -> pd.DataFrame:
    return load_processed()


@st.cache_resource
def get_model(elo_weight: float, poisson_weight: float, data_version: str, _matches: pd.DataFrame) -> EnsemblePredictor:
    # load_or_fit reusa un modelo entrenado desde data/model_cache/ si ya existe
    # uno para estos mismos datos + parámetros; si no, entrena y lo guarda.
    # @st.cache_resource evita repetir esto entre interacciones dentro de una
    # misma sesión; load_or_fit evita reentrenar entre arranques distintos del
    # dashboard (ej. tras reiniciar el proceso de streamlit). data_version va
    # en la firma para que un partido nuevo no siga usando el modelo anterior.
    return load_or_fit(_matches, elo_weight=elo_weight, poisson_weight=poisson_weight)


st.title("Liga MX Predictor")

with st.sidebar:
    st.header("Configuración")
    elo_weight = st.slider("Peso del modelo Elo", 0.0, 1.0, 0.5, 0.05)
    poisson_weight = round(1 - elo_weight, 2)
    st.write(f"Peso del modelo Poisson: **{poisson_weight}**")

skeleton = st.empty()
with skeleton.container():
    show_skeleton()

matches = get_matches()
tournament = current_tournament(matches)
teams = get_team_list(tournament)
table = standings(tournament)
last_match = matches["date"].max()

skeleton.empty()

st.caption(f"Ensemble (Elo + Poisson) — datos hasta el {last_match:%d/%m/%Y}")

model = get_model(elo_weight, poisson_weight, f"{last_match:%Y-%m-%d}-{len(matches)}", matches)

col1, col2 = st.columns(2)
with col1:
    home_team = st.selectbox("Equipo local", teams, index=teams.index("América") if "América" in teams else 0)
with col2:
    away_team = st.selectbox("Equipo visitante", teams, index=teams.index("Chivas") if "Chivas" in teams else 1)

if home_team == away_team:
    st.warning("Selecciona dos equipos diferentes.")
else:
    result = model.predict(home_team, away_team)

    st.subheader(f"{home_team} - {away_team}")

    probs_df = pd.DataFrame({
        "Resultado": [f"Gana {home_team}", "Empate", f"Gana {away_team}"],
        "Probabilidad": [
            result["ensemble"]["home_win"],
            result["ensemble"]["draw"],
            result["ensemble"]["away_win"],
        ],
    })

    fig = px.bar(probs_df, x="Resultado", y="Probabilidad", text_auto=".1%", color="Resultado")
    fig.update_layout(showlegend=False, yaxis_tickformat=".0%")
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Gana {home_team}", f"{result['ensemble']['home_win']:.1%}")
    c2.metric("Empate", f"{result['ensemble']['draw']:.1%}")
    c3.metric(f"Gana {away_team}", f"{result['ensemble']['away_win']:.1%}")

    top_scores = result["poisson"]["top_scores"]
    top_scores_str = "  ·  ".join(f"**{score}** ({prob:.1%})" for score, prob in top_scores)
    st.info(f"Marcadores más probables (modelo Poisson): {top_scores_str}")

    with st.expander("Ver desglose por modelo (Elo vs Poisson)"):
        st.json({"Elo": result["elo"], "Poisson": result["poisson"]})

    with st.expander("Historial de enfrentamientos directos"):
        h2h = head_to_head(matches, home_team, away_team)
        if h2h.empty:
            st.write("Sin enfrentamientos previos registrados.")
        else:
            st.dataframe(
                h2h[["date", "home_team", "away_team", "home_score", "away_score"]],
                width="stretch",
            )

st.divider()
st.subheader(f"Tabla general — {tournament_name(tournament)}")
st.caption(f"Los {LIGUILLA_TEAMS} primeros clasifican directo a la liguilla.")
st.dataframe(table, width="stretch")

st.divider()
st.subheader("Simulador de liguilla")
st.caption(
    "Parte del top 8 actual de la tabla; puedes cambiarlo para probar otros "
    "escenarios. El orden importa: es la siembra del 1° al 8°."
)

seeded = st.multiselect(
    "Equipos clasificados (en orden: 1° a 8°)",
    options=teams,
    default=table["Equipo"].head(LIGUILLA_TEAMS).tolist(),
    max_selections=LIGUILLA_TEAMS,
)

if len(seeded) == LIGUILLA_TEAMS:
    n_sims = st.slider("Número de simulaciones", 500, 5000, 2000, 500)
    if st.button("Simular liguilla"):
        with st.spinner("Simulando..."):
            probs = simulate_liguilla(model, seeded, n_simulations=n_sims)
        probs_df = pd.DataFrame(
            {"Equipo": list(probs.keys()), "Prob. de ser campeón": list(probs.values())}
        ).sort_values("Prob. de ser campeón", ascending=False)
        fig2 = px.bar(probs_df, x="Equipo", y="Prob. de ser campeón", text_auto=".1%")
        fig2.update_layout(yaxis_tickformat=".0%")
        st.plotly_chart(fig2, width="stretch")
else:
    st.info(f"Selecciona exactamente {LIGUILLA_TEAMS} equipos para simular la liguilla.")
