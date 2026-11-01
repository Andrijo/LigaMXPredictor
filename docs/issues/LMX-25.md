---
title: [LMX-25] Crear un modelo de posesión con Markov (xT)
labels: modelo,prioridad:baja
---

## Contexto

La amenaza esperada (xT) valora cada zona según la probabilidad de terminar en gol. Requiere el registro completo de pases, que solo existe desde algún punto de 2025-26.

## Qué hacer

- [ ] Definir la rejilla del campo y las acciones.
- [ ] Estimar transiciones y resolver el valor por zona.
- [ ] Calcular el valor aportado por equipo y jugador.

## Criterios de aceptación

- [ ] El mapa de valor se revisa contra el resultado esperado de la zona.
- [ ] El tamaño de muestra se reporta junto con el resultado.

## Depende de

- LMX-17: Crear el módulo de eventos de ESPN

## Nota

Conviene esperar a tener varios torneos completos. LMX-17 debe indicar cuántos partidos hay.
