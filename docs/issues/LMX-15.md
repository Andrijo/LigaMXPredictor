---
title: [LMX-15] Propagar la incertidumbre en las simulaciones
labels: modelo,prioridad:media
---

## Contexto

Las simulaciones mantienen fijas las fuerzas e ignoran a Elo. Esto puede volverlas demasiado seguras: en la validación, los casos de 50-70% clasificaron 33% de las veces, aunque fueron apenas 12.

## Qué hacer

- [ ] Variar las fuerzas entre simulaciones.
- [ ] Evaluar si los goles esperados deben incorporar la señal de Elo.
- [ ] Modelar tiempos extra y penales de la final en vez de usar 50/50.

## Criterios de aceptación

- [ ] Se repite la validación con torneos pasados, a la misma altura de cada torneo.
- [ ] Mejora o iguala el Brier actual de 0.074 y la calibración.

## Depende de

- LMX-09: Crear un marco de evaluación común
