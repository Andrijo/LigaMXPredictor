---
title: [LMX-13] Entrenar el modelo con los resultados recientes de ESPN
labels: modelo,prioridad:media
---

## Contexto

Los resultados de ESPN actualizan la tabla, pero el modelo solo aprende de football-data, que puede ir varios días atrás.

## Qué hacer

- [ ] Sumar esos partidos al entrenamiento.
- [ ] Evitar duplicados cuando lleguen a football-data.

## Criterios de aceptación

- [ ] Un resultado reciente cambia las fuerzas el mismo día.
- [ ] Un partido presente en ambas fuentes cuenta una sola vez.
- [ ] La caché se invalida al llegar resultados nuevos.

## Depende de

- LMX-02: No reutilizar un calendario incompleto durante 24 horas
