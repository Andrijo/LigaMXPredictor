---
title: [LMX-07] Guardar predicciones antes de cada partido
labels: producto,prioridad:alta
---

## Contexto

El backtest quedó parcialmente contaminado porque los parámetros se eligieron con esos mismos años. Solo las predicciones guardadas antes de jugarse dan una medición limpia.

## Qué hacer

- [ ] Definir dónde guardar las predicciones sin alterar las ya registradas.
- [ ] Registrar fecha, versión del modelo, probabilidades y momio disponible.
- [ ] Cruzarlas con el resultado real cuando llegue.

## Criterios de aceptación

- [ ] Una predicción no se puede registrar después de iniciado el partido.
- [ ] El dashboard muestra log-loss, Brier y aciertos acumulados, comparados con el baseline y con el mercado si hay momios.

## Depende de

- LMX-06: Mostrar las predicciones de la próxima jornada

## Nota

Hay que decidir cómo se ejecuta cuando el dashboard está cerrado, por ejemplo con una tarea programada.
