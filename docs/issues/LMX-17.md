---
title: [LMX-17] Crear el módulo de eventos de ESPN
labels: datos,prioridad:alta
---

## Contexto

El feed no oficial de ESPN trae unas 200 jugadas por partido en las muestras de 2013 a 2025, y unas 1,400 con pases y coordenadas en agosto de 2026. Todavía no se sabe cuándo cambió, ni si los tiros antiguos traen coordenadas.

## Qué hacer

- [ ] Medir por torneo cuántas jugadas hay, de qué tipo y con qué coordenadas.
- [ ] Confirmar en qué fecha empieza el registro completo.
- [ ] Descargar todas las páginas con límite de velocidad y reanudación.
- [ ] Guardar los datos de forma que no se vuelvan a descargar.
- [ ] Vincular cada partido con football-data.

## Criterios de aceptación

- [ ] Existe una tabla de cobertura por torneo.
- [ ] Una descarga interrumpida se reanuda sin repetir lo guardado.
- [ ] Al menos 99% de los partidos queda vinculado y el resto se reporta.
- [ ] Las pruebas no dependen de la red.

## Nota

Un partido completo son unas 59 páginas, cerca de 18,000 peticiones por temporada. Es una API no oficial: ver LMX-28.
