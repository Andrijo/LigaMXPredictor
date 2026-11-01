---
title: [LMX-24] Modelar la dinámica dentro del partido con state-space
labels: modelo,prioridad:baja
---

## Contexto

Va más allá de la cadena de Markov: la intensidad de cada equipo cambia con el marcador, el tiempo y las expulsiones.

## Qué hacer

- [ ] Definir el modelo de intensidad por equipo.
- [ ] Incluir los cambios por marcador y expulsiones.
- [ ] Actualizar la estimación con cada evento.

## Criterios de aceptación

- [ ] Se compara con LMX-23 en la misma evaluación por minuto.
- [ ] Se adopta solo si supera a la cadena de Markov.

## Depende de

- LMX-11: Modelar fuerzas dinámicas con state-space
- LMX-23: Crear una cadena de Markov por marcador
