---
title: [LMX-23] Crear una cadena de Markov por marcador
labels: modelo,prioridad:media
---

## Contexto

Con los minutos de gol se puede modelar cómo cambia el marcador durante el partido y estimar las probabilidades en cualquier minuto.

## Qué hacer

- [ ] Extraer minutos de goles y expulsiones.
- [ ] Estimar transiciones según marcador, minuto y fuerza previa.
- [ ] Validar contra el resultado final.

## Criterios de aceptación

- [ ] Las probabilidades del minuto 0 coinciden con las del modelo previo al partido.
- [ ] El log-loss mejora conforme avanza el partido, y se reporta por minuto.

## Depende de

- LMX-09: Crear un marco de evaluación común
- LMX-17: Crear el módulo de eventos de ESPN
