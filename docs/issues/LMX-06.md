---
title: [LMX-06] Mostrar las predicciones de la próxima jornada
labels: producto,prioridad:alta
---

## Contexto

`src/fixtures.py` ya obtiene el calendario, pero el dashboard obliga a elegir los equipos a mano.

## Qué hacer

- [ ] Agrupar los partidos pendientes por fecha.
- [ ] Mostrar probabilidades 1X2 y marcador más probable de cada uno.

## Criterios de aceptación

- [ ] El dashboard lista la próxima jornada sin elegir equipos.
- [ ] Sin calendario, la sección muestra un aviso y el resto sigue funcionando.

## Depende de

- LMX-02: No reutilizar un calendario incompleto durante 24 horas
