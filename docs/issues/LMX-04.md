---
title: [LMX-04] Fijar las versiones de las dependencias
labels: mantenimiento,prioridad:media
---

## Contexto

`requirements.txt` solo define versiones mínimas, así que una instalación futura puede comportarse distinto a la probada.

## Qué hacer

- [ ] Definir versiones exactas o un archivo de bloqueo.
- [ ] Usar esas versiones en GitHub Actions.

## Criterios de aceptación

- [ ] Dos instalaciones limpias obtienen las mismas versiones.
- [ ] Las pruebas pasan en CI con esas versiones.
