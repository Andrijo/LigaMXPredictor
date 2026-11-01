---
title: [LMX-14] Aprender los pesos del ensemble y los empates de Elo
labels: modelo,prioridad:media
---

## Contexto

El ensemble pesa 50/50 y Elo calcula empates con una fórmula fija.

## Qué hacer

- [ ] Aprender los pesos con una regresión logística u otro método simple.
- [ ] Ajustar la probabilidad de empate con datos históricos.

## Criterios de aceptación

- [ ] Los pesos se aprenden solo con datos pasados.
- [ ] Se adopta solo si mejora la evaluación común.

## Depende de

- LMX-09: Crear un marco de evaluación común

## Nota

Las pruebas con pesos fijos entre 0.35 y 0.65 dieron diferencias pequeñas. Puede no haber mucho que ganar.
