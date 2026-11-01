---
title: [LMX-05] Retirar las referencias a master y al nombre anterior
labels: mantenimiento,prioridad:baja
---

## Contexto

El repositorio ya se llama `LigaMXPredictor` y solo queda la rama `main`, pero `.github/workflows/tests.yml` todavía incluye `master`.

## Qué hacer

- [ ] Dejar solo `main` en el workflow.
- [ ] Buscar menciones restantes a `WC26Predictor` o `master` en el repositorio.

## Criterios de aceptación

- [ ] El workflow solo corre sobre `main` y los pull requests.
- [ ] No quedan referencias al nombre anterior.
