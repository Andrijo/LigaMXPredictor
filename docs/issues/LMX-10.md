---
title: [LMX-10] Medir la calibración de la predicción 1X2
labels: investigación,prioridad:media
---

## Contexto

El log-loss no muestra si lo que el modelo da como 60% ocurre cerca del 60% de las veces. La proyección de clasificados sí se revisó, pero el 1X2 no.

## Qué hacer

- [ ] Generar una tabla de calibración por resultado.
- [ ] Si hay desviación clara, probar una recalibración y evaluarla.

## Criterios de aceptación

- [ ] El backtest incluye la calibración de cada resultado.
- [ ] Una recalibración solo se adopta si mejora fuera de muestra.

## Depende de

- LMX-09: Crear un marco de evaluación común
