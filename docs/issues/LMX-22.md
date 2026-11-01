---
title: [LMX-22] Definir y evaluar modelos de reglas de decisión
labels: investigación,prioridad:baja
---

## Contexto

El término puede significar reglas interpretables tipo RuleFit o reglas para decidir apuestas, y cada una necesita cosas distintas.

## Qué hacer

- [ ] Decidir el objetivo antes de implementar.
- [ ] Si son interpretables, mostrar reglas legibles y compararlas con el ensemble.
- [ ] Si son de apuestas, conseguir momios de apertura o en tiempo real.

## Criterios de aceptación

- [ ] El alcance queda escrito en este issue.
- [ ] Las reglas se evalúan fuera de muestra.
- [ ] Una regla de apuestas se simula con momios disponibles antes del partido.

## Depende de

- LMX-09: Crear un marco de evaluación común
- LMX-18: Construir la tabla de variables sin fuga de información

## Nota

El CSV solo trae momios de cierre y el modelo no les gana, así que hoy no hay base para una estrategia de apuestas.
