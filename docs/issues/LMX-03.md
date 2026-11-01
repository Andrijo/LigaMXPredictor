---
title: [LMX-03] Invalidar y limpiar la caché de modelos
labels: mantenimiento,prioridad:media
---

## Contexto

La llave de `model_cache.py` cubre datos y configuración, pero no el código. Si cambia el modelo, se puede servir un pickle viejo. Además, cada día de datos y cada posición del control de pesos crean un archivo nuevo que nunca se borra.

## Qué hacer

- [ ] Incluir una versión del modelo en la llave de caché.
- [ ] Borrar los modelos entrenados con datos anteriores.

## Criterios de aceptación

- [ ] Un cambio de versión obliga a reentrenar.
- [ ] La carpeta `data/model_cache/` no crece sin límite.
