---
title: [LMX-26] Implementar una versión de EPV basada en eventos
labels: investigación,prioridad:baja
---

## Contexto

El EPV real necesita tracking de los 22 jugadores, que no encontré disponible para Liga MX. Con eventos solo se puede hacer una aproximación tipo xT o VAEP.

## Qué hacer

- [ ] Decidir si la aproximación aporta algo frente a LMX-25.
- [ ] Si aporta, entrenarla con eventos y xG.
- [ ] Documentar que no equivale a un EPV con tracking.

## Criterios de aceptación

- [ ] El resultado se llama por lo que es, no EPV a secas.
- [ ] Se muestra la ganancia frente a xT.

## Depende de

- LMX-19: Entrenar un modelo Spatial xG
- LMX-25: Crear un modelo de posesión con Markov (xT)

## Nota

Es lo último de la lista. Queda bloqueado para un EPV real hasta conseguir tracking.
