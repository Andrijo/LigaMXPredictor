---
title: [LMX-09] Crear un marco de evaluación común
labels: investigación,prioridad:alta
---

## Contexto

Cada comparación se ha hecho con scripts sueltos. Para sumar modelos nuevos hace falta una prueba única que no se pueda ajustar a conveniencia.

## Qué hacer

- [ ] Evaluar por torneo con walk-forward, contra baseline y mercado.
- [ ] Reportar intervalos por bootstrap, no solo promedios.
- [ ] Reservar un periodo final que no se use para elegir parámetros.
- [ ] Permitir registrar un modelo nuevo sin duplicar lógica.

## Criterios de aceptación

- [ ] Cualquier modelo se compara con un solo comando.
- [ ] El reporte indica si la diferencia es distinguible de cero.
- [ ] La evaluación reproduce los resultados actuales del ensemble.
