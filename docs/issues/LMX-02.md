---
title: [LMX-02] No reutilizar un calendario incompleto durante 24 horas
labels: datos,prioridad:alta
---

## Contexto

`load_fixtures` guarda lo que devuelve ESPN aunque falten cruces, y esa copia se considera vigente durante 24 horas. Un fallo parcial deja la proyección desactivada todo un día.

## Qué hacer

- [ ] Considerar vigente la copia local solo si cubre todos los cruces pendientes.
- [ ] Si la copia está incompleta, volver a consultar ESPN.

## Criterios de aceptación

- [ ] Con una copia incompleta y reciente se hace una nueva consulta.
- [ ] Si ESPN sigue fallando, el dashboard mantiene el aviso y no se rompe.
- [ ] Hay una prueba para cada caso.
