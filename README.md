# P1L1_Grupo4

Modelo 3D del edificio - Proyecto 1 Grupo 4.
Analisis elastico lineal de un edificio de hormigon armado en OpenSeesPy.

## Sistema de unidades

SI coherente:

| Magnitud | Unidad |
|---|---|
| longitud | m |
| fuerza | kN |
| tension / modulo | kN/m2 |
| momento | kN*m |

## Instalacion

```powershell
git clone <URL-del-repo>.git
cd P1L1_Grupo4
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```powershell
.venv\Scripts\Activate.ps1
python -m src.building_analysis
```

Salidas:
- `results/figures/edificio_3d.png`: geometria, deformada y apoyos.

## Estructura del edificio

- 6 columnas cuadradas 70x70 cm
- Vigas rectangulares 60x80 cm
- 5 niveles: base (Z=0), sub1 (Z=3.96m), piso1-4 (hasta Z=19.80m)
- Material: H30 (f'c = 25 MPa, Ec = 23.5 GPa)
- Diafragmas rigidos en cada nivel suspendido
- Carga: peso propio de losas (15 cm)

## Estructura

```
src/     building_analysis.py - modelo, analisis y visualizacion
results/ figuras de salida
```

## Sistema operativo y Python

- Windows 11
- Python 3.12
- OpenSeesPy 3.8.0
