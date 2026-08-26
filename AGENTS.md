# AGENTS.md

Instrucciones para que OpenCode trabaje en este repositorio.

## Proposito del proyecto

Estructura simple de hormigon armado con losa maciza modelada con
elementos shell (shellMITC4) en OpenSeesPy.
Analisis elastico lineal del peso propio de la losa, demostrando
la transferencia de esfuerzos: losa -> vigas -> columnas.

## Sistema de unidades

SI coherente: longitud m, fuerza kN, tension/modulo kN/m2, momento kN*m.
No mezclar nunca m con mm ni kN con N.

## Reglas

- Mantener el codigo sencillo y legible.
- Los datos de la estructura estan en `data/estructura_simple.json`.
- El modelo completo (malla, elementos, analisis) esta en `src/simple_analysis.py`.
- No inventar mediciones: todos los valores deben salir de ejecuciones reales.
- Ejecutar el analisis: `python -m src.simple_analysis`.
- No ejecutar comandos destructivos de Git sin permiso explicito.
- No subir credenciales ni informacion sensible.
