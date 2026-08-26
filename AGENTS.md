# AGENTS.md

Instrucciones para que OpenCode trabaje en este repositorio.

## Propósito del proyecto

Pórtico 3D de hormigón armado (1 piso, 1 vano, 3×6 m) analizado con OpenSeesPy.
El peso propio de la losa se aplica como carga distribuida en vigas via
`eleLoad -beamUniform`, demostrando el camino de carga: losa → vigas → columnas.

## Sistema de unidades

SI coherente: longitud m, fuerza kN, tensión/módulo kN/m², momento kN·m.
No mezclar nunca m con mm ni kN con N.

## Reglas

- Mantener el código sencillo y legible.
- Los datos del pórtico están en `data/portico_3d.json`.
- El modelo completo está en `src/portico_3d.py`.
- No inventar mediciones: todos los valores deben salir de ejecuciones reales.
- Ejecutar el análisis: `python -m src.portico_3d`.
- No ejecutar comandos destructivos de Git sin permiso explícito.
- No subir credenciales ni información sensible.
