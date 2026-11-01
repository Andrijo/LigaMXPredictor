---
title: [LMX-18] Construir la tabla de variables sin fuga de información
labels: datos,prioridad:alta
---

## Contexto

Boosting, reglas de decisión y xG necesitan variables calculadas por partido. Si incluyen información posterior al inicio, el backtest se verá mejor de lo real.

## Qué hacer

- [ ] Definir variables de forma reciente, descanso, localía y fuerza.
- [ ] Calcular cada una solo con lo disponible antes del partido.
- [ ] Decidir si los momios serán variable o solo referencia.

## Criterios de aceptación

- [ ] Hay una prueba que falla si una variable usa datos futuros.
- [ ] Cada variable tiene definición y fecha de disponibilidad.

## Depende de

- LMX-09: Crear un marco de evaluación común
- LMX-17: Crear el módulo de eventos de ESPN
