---
title: [LMX-01] Conservar los resultados de las simulaciones en el dashboard
labels: producto,prioridad:alta
---

## Contexto

Los resultados se dibujan dentro de `if st.button(...)`. Al mover cualquier control, Streamlit vuelve a ejecutar la página y la simulación desaparece.

## Qué hacer

- [ ] Guardar la proyección y la liguilla en `st.session_state`.
- [ ] Mostrar con qué parámetros se generó cada resultado.

## Criterios de aceptación

- [ ] Cambiar los equipos del predictor no borra una simulación ya hecha.
- [ ] Una simulación de otra configuración no se muestra como si fuera la actual.
