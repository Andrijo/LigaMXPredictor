---
title: [LMX-11] Modelar fuerzas dinámicas con state-space
labels: modelo,prioridad:alta
---

## Contexto

Hoy las fuerzas cambian solo por el decaimiento temporal del Poisson. Un modelo state-space las trata como procesos que evolucionan y además da su incertidumbre. Es lo más prometedor sin datos nuevos, pero es una hipótesis sin medir.

## Qué hacer

- [ ] Implementar el filtro sobre la serie de resultados.
- [ ] Elegir la varianza del proceso con el periodo de entrenamiento.
- [ ] Exponer la incertidumbre de la fuerza de cada equipo.

## Criterios de aceptación

- [ ] Se compara con el Poisson actual en log-loss 1X2 y de marcador exacto.
- [ ] Se adopta solo si mejora con un intervalo que excluya el cero.
- [ ] Si no mejora, queda documentado el resultado.

## Depende de

- LMX-09: Crear un marco de evaluación común
