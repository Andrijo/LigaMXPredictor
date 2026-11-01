---
title: [LMX-19] Entrenar un modelo Spatial xG
labels: modelo,prioridad:alta
---

## Contexto

Con coordenadas de tiro se puede estimar la probabilidad de gol de cada disparo. No hay posiciones de defensas ni portero, así que será un xG de ubicación y contexto, más limitado que uno comercial.

## Qué hacer

- [ ] Extraer ubicación, parte del cuerpo y tipo de jugada de los tiros.
- [ ] Definir qué hacer con penales y autogoles.
- [ ] Entrenar un modelo base y uno con LightGBM o XGBoost.
- [ ] Comprobar si los datos anteriores y posteriores al cambio de formato son comparables.

## Criterios de aceptación

- [ ] Se evalúa fuera de muestra con log-loss y calibración.
- [ ] La suma de xG se acerca a los goles reales.
- [ ] El modelo no usa información posterior al tiro.

## Depende de

- LMX-09: Crear un marco de evaluación común
- LMX-17: Crear el módulo de eventos de ESPN

## Nota

Solo se puede iniciar si LMX-17 confirma las coordenadas de los tiros.
