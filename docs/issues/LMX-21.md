---
title: [LMX-21] Probar XGBoost y LightGBM para predecir partidos
labels: modelo,prioridad:media
---

## Contexto

Ambas librerías tienen versiones instalables para Python 3.14. Con unos 4,800 partidos hay riesgo de sobreajuste y no se espera un gran salto.

## Qué hacer

- [ ] Entrenar un modelo con variables base.
- [ ] Probarlo con xG agregado cuando LMX-19 esté listo.
- [ ] Probarlo como modelo independiente y como parte del ensemble.

## Criterios de aceptación

- [ ] Se usa la evaluación común sin tocar el periodo reservado.
- [ ] Se adopta solo si mejora con un intervalo que excluya el cero.
- [ ] Las predicciones se calibran antes de combinarlas.

## Depende de

- LMX-09: Crear un marco de evaluación común
- LMX-18: Construir la tabla de variables sin fuga de información

## Nota

Basta con una librería. Elegir la que funcione mejor.
