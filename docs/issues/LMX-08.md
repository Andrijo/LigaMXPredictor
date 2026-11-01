---
title: [LMX-08] Calcular xPoints antes del partido
labels: modelo,prioridad:media
---

## Contexto

La matriz de marcadores ya permite calcular los puntos esperados: 3 × P(ganar) + P(empatar).

## Qué hacer

- [ ] Agregar `expected_points` al predictor.
- [ ] Mostrar en el dashboard los puntos esperados contra los puntos reales por equipo.

## Criterios de aceptación

- [ ] Los puntos esperados de ambos equipos coinciden con la matriz de marcadores.
- [ ] Hay pruebas con matrices conocidas.

## Nota

Estos xPoints miden lo que se esperaba antes del partido. Los que usan los tiros reales son LMX-20.
