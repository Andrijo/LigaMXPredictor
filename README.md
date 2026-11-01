# Liga MX Match Predictor

Proyecto de práctica diaria en Python: predicción de partidos de Liga MX con un
ensemble Elo + Poisson (Dixon-Coles), usando todos los partidos de Primera
División desde el Apertura 2012, más un simulador de liguilla Monte Carlo.

## Estructura del proyecto

```
.
├── data/
│   ├── raw/              # datos crudos descargados
│   └── processed/        # datos limpios listos para modelar
├── src/
│   ├── data_loader.py    # descarga, limpieza y actualización de datos
│   ├── elo.py             # Day 1 - modelo Elo
│   ├── poisson_model.py   # Day 2 - modelo de goles Poisson (Dixon-Coles)
│   ├── ensemble.py        # Day 3 - combina Elo + Poisson
│   ├── league_config.py   # parámetros de Liga MX y nombres de equipos
│   ├── backtest.py        # validación walk-forward fuera de muestra
│   ├── liguilla.py        # simulador de liguilla Monte Carlo
│   ├── model_cache.py     # persistencia de modelos entrenados en disco
│   └── utils.py           # tabla general, torneos y utilidades
├── app/
│   └── dashboard.py       # interfaz interactiva con Streamlit
├── tests/                 # tests unitarios
├── requirements.txt
└── README.md
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

### 1. Descargar los datos

```bash
python -m src.data_loader
```

Es opcional: si los datos faltan o tienen más de 24 horas, se actualizan solos
al cargarlos. Si la descarga falla, se sigue con la copia local.

### 2. Ejecutar el dashboard interactivo

```bash
streamlit run app/dashboard.py
```

Si el comando `streamlit` no se reconoce (error `command not found` porque el
script no quedó en el `PATH`, algo común con `pip install --user` o en algunos
entornos virtuales), use el módulo directamente con el mismo intérprete de
Python donde lo instalaste:

```bash
python -m streamlit run app/dashboard.py
```

El dashboard incluye predicción por partido, tabla general del torneo en curso
y simulador de liguilla a partir del top 8 actual.

### 3. Backtesting walk-forward

```bash
python -m src.backtest --start-year 2018
```

Valida el modelo fuera de muestra: entrena con todo lo anterior a cada
trimestre, predice sus partidos, y repite. Calcula log-loss, Brier score y
accuracy comparando Elo, Poisson, ensemble, un baseline ingenuo y el mercado
(momio promedio de cierre).

Resultados con datos hasta octubre de 2026 (2,943 partidos desde 2018):

| Modelo   | Log-loss | Brier  | Accuracy |
|----------|----------|--------|----------|
| Ingenuo  | 1.0697   | 0.6464 | 45.2%    |
| Elo      | 1.0303   | 0.6175 | 49.2%    |
| Poisson  | 1.0278   | 0.6166 | 48.9%    |
| Ensemble | 1.0242   | 0.6142 | 49.4%    |
| Mercado  | 1.0079   | 0.6032 | 50.5%    |

El ensemble le gana con claridad al baseline, pero sigue lejos del mercado: no
sirve para encontrar valor contra las casas de apuestas.

Los parámetros de `LIGA_MX` salieron de este backtest: `home_advantage=60`, bonus
de altitud en 0 (con 25 empeoraba Elo tanto en 2018-2023 como en 2024-2026),
y Poisson con vida media de 730 días y `ridge=16`, elegidos por log-loss de
marcador exacto en 2018-2023.

El Poisson por máxima verosimilitud mejora el marcador exacto (-0.0134 en todo el
periodo, IC 95% de -0.0197 a -0.0071), que es lo que usa el simulador de liguilla.
En 2024-2026 la mejora es menor y no concluyente (-0.0069, IC 95% de -0.0199 a
+0.0057). En el ensemble 1X2 la diferencia está dentro del ruido.

### 4. Simulación de liguilla

```bash
python -m src.liguilla
```

Simula cuartos, semis y final con Monte Carlo sobre la matriz de marcadores del
modelo Poisson y devuelve la probabilidad de campeonar de cada equipo. Sigue el
formato vigente, verificado contra las liguillas de 2023 a 2026:

- Clasifican directo los 8 primeros, sin Play-In.
- Cuartos: 1 vs 8, 2 vs 7, 3 vs 6, 4 vs 5.
- En semis se reacomoda el cuadro: el mejor sembrado vivo enfrenta al peor.
- El mejor sembrado cierra en casa.
- Con global empatado, en cuartos y semis pasa el mejor sembrado. En la final
  hay tiempos extra y penales (aproximados con 50/50). No hay gol de visitante.

El peso de Elo del dashboard no afecta esta simulación, porque Elo no predice
marcadores.

### 5. Caché de modelos

El dashboard usa `model_cache.py` para persistir el modelo entrenado en disco.
La caché se invalida automáticamente si cambian los datos o los parámetros.

```bash
python -m src.model_cache   # benchmark: primera carga vs. desde caché
```

### 6. Uso desde Python

```python
from src.data_loader import load_processed
from src.ensemble import EnsemblePredictor

matches = load_processed()
model = EnsemblePredictor().fit(matches)
model.predict("América", "Chivas")
```

Los nombres de los equipos son los de `TEAM_NAMES` en `src/league_config.py`.

### 7. Tests

```bash
python -m pytest tests
```

## Fuente de datos

Resultados y momios de cierre de [football-data.co.uk](https://www.football-data.co.uk/mexico.php):
fase regular y liguilla desde 2012/13. La fuente no marca qué partidos son de
liguilla, por eso la tabla general toma los primeros 153 partidos de cada torneo.
Tampoco trae calendario: solo partidos ya jugados, y puede ir unos días atrás.
