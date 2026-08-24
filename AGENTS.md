# AGENTS.md

Instrucciones para que OpenCode trabaje en este repositorio.

## Propósito del proyecto

P1L1 - LAB: construir y verificar un benchmark estructural 3D en OpenSeesPy,
reproduciendo el caso definido por el profesor (tutorial de OpenSees, Semana 1):
voladizo 3D verificado analíticamente más un marco 3D mínimo para ejercitar
ejes locales, fuerza axial y momentos de extremo.

## Sistema de unidades

SI coherente: longitud m, fuerza kN, tensión/módulo kN/m², momento kN·m.
No mezclar nunca m con mm ni kN con N.

## Reglas

- Mantener el código sencillo y legible.
- Los datos del modelo viven en `data/*.json`; no hardcodear geometría en el código.
- No inventar mediciones: todos los valores deben salir de ejecuciones reales.
- Los valores de referencia provienen de soluciones analíticas documentadas
  (`src/reference.py`); no modificarlos sin justificación escrita.
- Validar el contrato de fuerzas locales antes de nombrar componentes
  (ver README: contrato validado numéricamente).
- Ejecutar las pruebas después de modificar código: `pytest`.
- No ejecutar comandos destructivos de Git sin permiso explícito.
- No subir credenciales ni información sensible.
