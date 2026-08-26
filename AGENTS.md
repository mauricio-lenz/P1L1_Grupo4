# AGENTS.md

Instrucciones para que OpenCode trabaje en este repositorio.

## Proposito del proyecto

Modelo 3D de un edificio de hormigon armado en OpenSeesPy.
Analisis elastico lineal con peso propio de losas, diafragmas rigidos y
extraccion de desplazamientos, reacciones y fuerzas de elementos.

## Sistema de unidades

SI coherente: longitud m, fuerza kN, tension/modulo kN/m2, momento kN*m.
No mezclar nunca m con mm ni kN con N.

## Reglas

- Mantener el codigo sencillo y legible.
- Los datos geometricos del edificio estan en `src/building_analysis.py`.
- No inventar mediciones: todos los valores deben salir de ejecuciones reales.
- Ejecutar el analisis: `python -m src.building_analysis`.
- No ejecutar comandos destructivos de Git sin permiso explicito.
- No subir credenciales ni informacion sensible.
