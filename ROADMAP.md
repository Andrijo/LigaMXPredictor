# Roadmap

Lo que falta implementar en el predictor de Liga MX. Cada elemento tiene su issue en `docs/issues/`, listo para publicar en GitHub.

**Para marcar un avance:** cambia `[ ]` por `[x]` en la tabla. Las mejoras de modelo son hipótesis: solo se adoptan si superan la evaluación común (LMX-09).

## Ya implementado

- Ensemble de Elo y Poisson por máxima verosimilitud, con decaimiento temporal.
- Backtest walk-forward contra baseline y momios de cierre.
- Tabla general con resultados recientes de ESPN.
- Simulador de liguilla con las reglas vigentes.
- Proyección del resto del torneo.
- Pruebas automáticas y GitHub Actions.

## Orden recomendado

Empezar por **LMX-01** y **LMX-02**, seguir con **LMX-06**, **LMX-07** y **LMX-09**, y después **LMX-11** y **LMX-17**.

## Fase 0: arreglos y orden

Problemas conocidos del código y del repo. Son pequeños y no dependen de nada.

| Hecho | ID | Tarea | Prioridad | Depende de |
|---|---|---|---|---|
| [ ] | [LMX-01](docs/issues/LMX-01.md) | Conservar los resultados de las simulaciones en el dashboard | Alta | — |
| [ ] | [LMX-02](docs/issues/LMX-02.md) | No reutilizar un calendario incompleto durante 24 horas | Alta | — |
| [ ] | [LMX-03](docs/issues/LMX-03.md) | Invalidar y limpiar la caché de modelos | Media | — |
| [ ] | [LMX-04](docs/issues/LMX-04.md) | Fijar las versiones de las dependencias | Media | — |
| [ ] | [LMX-05](docs/issues/LMX-05.md) | Retirar las referencias a master y al nombre anterior | Baja | — |

## Fase 1: mejoras sin datos nuevos

Se pueden hacer con los resultados, momios y calendario que ya existen.

| Hecho | ID | Tarea | Prioridad | Depende de |
|---|---|---|---|---|
| [ ] | [LMX-06](docs/issues/LMX-06.md) | Mostrar las predicciones de la próxima jornada | Alta | LMX-02 |
| [ ] | [LMX-07](docs/issues/LMX-07.md) | Guardar predicciones antes de cada partido | Alta | LMX-06 |
| [ ] | [LMX-08](docs/issues/LMX-08.md) | Calcular xPoints antes del partido | Media | — |
| [ ] | [LMX-09](docs/issues/LMX-09.md) | Crear un marco de evaluación común | Alta | — |
| [ ] | [LMX-10](docs/issues/LMX-10.md) | Medir la calibración de la predicción 1X2 | Media | LMX-09 |
| [ ] | [LMX-11](docs/issues/LMX-11.md) | Modelar fuerzas dinámicas con state-space | Alta | LMX-09 |
| [ ] | [LMX-12](docs/issues/LMX-12.md) | Dar un rating inicial realista a equipos que regresan | Media | LMX-09 |
| [ ] | [LMX-13](docs/issues/LMX-13.md) | Entrenar el modelo con los resultados recientes de ESPN | Media | LMX-02 |
| [ ] | [LMX-14](docs/issues/LMX-14.md) | Aprender los pesos del ensemble y los empates de Elo | Media | LMX-09 |
| [ ] | [LMX-15](docs/issues/LMX-15.md) | Propagar la incertidumbre en las simulaciones | Media | LMX-09 |
| [ ] | [LMX-16](docs/issues/LMX-16.md) | Contemplar sanciones y todos los desempates en la tabla | Baja | — |

## Fase 2: datos de eventos

Requieren descargar jugadas de ESPN. LMX-17 desbloquea casi todo lo demás.

| Hecho | ID | Tarea | Prioridad | Depende de |
|---|---|---|---|---|
| [ ] | [LMX-17](docs/issues/LMX-17.md) | Crear el módulo de eventos de ESPN | Alta | — |
| [ ] | [LMX-18](docs/issues/LMX-18.md) | Construir la tabla de variables sin fuga de información | Alta | LMX-09, LMX-17 |
| [ ] | [LMX-19](docs/issues/LMX-19.md) | Entrenar un modelo Spatial xG | Alta | LMX-09, LMX-17 |
| [ ] | [LMX-20](docs/issues/LMX-20.md) | Calcular xPoints después del partido | Media | LMX-08, LMX-19 |
| [ ] | [LMX-21](docs/issues/LMX-21.md) | Probar XGBoost y LightGBM para predecir partidos | Media | LMX-09, LMX-18 |
| [ ] | [LMX-22](docs/issues/LMX-22.md) | Definir y evaluar modelos de reglas de decisión | Baja | LMX-09, LMX-18 |

## Fase 3: dinámica dentro del partido

Trabajan con lo que ocurre minuto a minuto, no solo con el resultado final.

| Hecho | ID | Tarea | Prioridad | Depende de |
|---|---|---|---|---|
| [ ] | [LMX-23](docs/issues/LMX-23.md) | Crear una cadena de Markov por marcador | Media | LMX-09, LMX-17 |
| [ ] | [LMX-24](docs/issues/LMX-24.md) | Modelar la dinámica dentro del partido con state-space | Baja | LMX-11, LMX-23 |
| [ ] | [LMX-25](docs/issues/LMX-25.md) | Crear un modelo de posesión con Markov (xT) | Baja | LMX-17 |
| [ ] | [LMX-26](docs/issues/LMX-26.md) | Implementar una versión de EPV basada en eventos | Baja | LMX-19, LMX-25 |

## Transversal

No dependen del orden anterior, pero conviene revisarlas antes de publicar o de invertir en datos.

| Hecho | ID | Tarea | Prioridad | Depende de |
|---|---|---|---|---|
| [ ] | [LMX-27](docs/issues/LMX-27.md) | Incorporar fichajes, lesiones y calendario de otras competencias | Media | LMX-09 |
| [ ] | [LMX-28](docs/issues/LMX-28.md) | Revisar permisos de uso y publicar el dashboard | Alta | — |

## Bloqueos principales

- **LMX-09** (Crear un marco de evaluación común) desbloquea 11 tareas: LMX-10, LMX-11, LMX-12, LMX-14, LMX-15, LMX-18, LMX-19, LMX-21, LMX-22, LMX-23, LMX-27.
- **LMX-17** (Crear el módulo de eventos de ESPN) desbloquea 4 tareas: LMX-18, LMX-19, LMX-23, LMX-25.
- **LMX-18** (Construir la tabla de variables sin fuga de información) desbloquea 2 tareas: LMX-21, LMX-22.
- **LMX-19** (Entrenar un modelo Spatial xG) desbloquea 2 tareas: LMX-20, LMX-26.

## Límites conocidos

- **EPV real:** requiere tracking de jugadores y no encontré una fuente para Liga MX.
- **Spatial xG:** falta confirmar las coordenadas de tiros antiguos. Sin posiciones de defensas ni portero será más limitado que uno comercial.
- **Registro completo de pases:** las muestras indican que empezó en algún punto de la temporada 2025-26.
- **ESPN:** es una API no oficial que puede cambiar sin aviso.
- **Apuestas:** el modelo no le gana a los momios de cierre (log-loss 1.0242 contra 1.0079 desde 2018).

## Publicar los issues

Con [GitHub CLI](https://cli.github.com/) instalado y autenticado (`gh auth login`), desde la raíz del repositorio:

```bash
bash docs/issues/crear_issues.sh
```

El script crea las etiquetas y omite los issues que ya existan, así que se puede volver a correr.
