---
title: [LMX-28] Revisar permisos de uso y publicar el dashboard
labels: producto,prioridad:alta
---

## Contexto

El proyecto usa football-data.co.uk y una API no oficial de ESPN. Para uso personal el riesgo es menor, pero publicar el dashboard o descargar a gran escala cambia la situación.

## Qué hacer

- [ ] Revisar las condiciones de uso de ambas fuentes.
- [ ] Decidir qué datos pueden mostrarse o guardarse.
- [ ] Publicar en Streamlit Community Cloud u otra opción si procede.

## Criterios de aceptación

- [ ] Queda escrito qué permite cada fuente.
- [ ] El dashboard público funciona sin escribir datos sensibles en el repositorio.
- [ ] El README incluye el enlace y las atribuciones necesarias.

## Nota

Hacer la revisión antes de LMX-17 si los datos de eventos se van a publicar.
