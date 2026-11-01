---
title: [LMX-20] Calcular xPoints después del partido
labels: modelo,prioridad:media
---

## Contexto

Con el xG de cada tiro se puede simular cada partido y obtener los puntos que un equipo mereció según sus ocasiones.

## Qué hacer

- [ ] Simular cada partido a partir de sus tiros.
- [ ] Agregar xPoints y diferencia contra puntos reales a la tabla.

## Criterios de aceptación

- [ ] El dashboard muestra xPoints por equipo en el torneo.
- [ ] La diferencia con los puntos reales se calcula de forma reproducible.
- [ ] Se mide si los xPoints predicen mejor los puntos futuros que los puntos reales.

## Depende de

- LMX-08: Calcular xPoints antes del partido
- LMX-19: Entrenar un modelo Spatial xG
