# P1L1-lenz-mauricio

P1L1 - LAB: benchmark 3D OpenSees. Construccion y verificacion cuantitativa de
casos estructurales 3D en OpenSeesPy, con extraccion de desplazamientos,
reacciones y fuerzas internas, visualizacion simple y archivo de resultados de
verificacion.

## Sistema operativo y Python

- Sistema operativo: Windows 11
- Python: 3.14.3
- OpenSeesPy: 3.8.0 (`ops.version()`)

## Sistema de unidades

SI coherente en todo el proyecto:

| Magnitud | Unidad |
|---|---|
| longitud | m |
| fuerza | kN |
| tension / modulo | kN/m2 |
| momento | kN*m |

## Instalacion y reproduccion

```powershell
git clone <URL-del-repo>.git
cd P1L1-lenz-mauricio
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

Ejecutar un caso completo (modelo -> analisis -> verificaciones -> JSON + figura):

```powershell
python -m src.run_benchmark --caso data/voladizo.json
python -m src.run_benchmark --caso data/marco3d.json
```

Salidas por caso:

- `results/<caso>_verificacion.json`: desplazamientos, reacciones, fuerzas de
  elementos y tabla de verificaciones con errores y veredicto.
- `results/figures/<caso>.png`: geometria con numeracion de nodos, ejes
  locales de cada elemento (x rojo, y verde, z azul), apoyos (cuadrado morado),
  cargas (flecha naranjo) y deformada (escala aumentada).

Pruebas automaticas:

```powershell
pytest
```

## Casos

### Voladizo 3D (benchmark Semana 1, tutorial del profesor)

Viga de L = 3 m sobre el eje global X, seccion 0.30 x 0.50 m, empotrada en el
nodo 1, carga P = 10 kN hacia abajo en el nodo 2. E = 25 GPa, nu = 0.20.

Verificado contra la solucion cerrada de Euler-Bernoulli.

### Marco 3D minimo

Dos columnas de 4 m (seccion 0.40 x 0.40) empotradas en la base, separadas
6 m, unidas por una viga (0.30 x 0.50). Cargas nodales simultaneas en los
nodos superiores: 20 kN hacia abajo y 50 kN horizontales en +X cada uno
(100 kN laterales totales).

Verificado contra una solucion independiente de portico plano por rigidez
directa implementada desde cero (`src/reference.py`), que incluye deformacion
axial: es indispensable porque el vuelco estira/acorta las columnas e inclina
la cuerda de la viga; ignorarlo da errores del orden de 15%.

## Resultados observados

Errores relativos reales de la ultima ejecucion (ver JSON para el detalle).

Voladizo:

| Chequeo | OpenSees | Referencia | Error rel |
|---|---|---|---|
| desplazamiento punta uz | 1.152000e-03 m | 1.152000e-03 m | ~9e-16 |
| reaccion Rz apoyo | 10.000000 kN | 10.000000 kN | ~1e-15 |
| axial viga | 0 kN | 0 kN | 0 |
| momento extremo empotrado \|My\| | 30.000000 kN*m | 30.000000 kN*m | ~9e-16 |

Marco 3D:

| Chequeo | OpenSees | Referencia | Error rel |
|---|---|---|---|
| deriva ux nodos 3 y 4 | 7.202980e-03 m | 7.202980e-03 m | ~3e-15 |
| axial columna barlovento (11) | +8.437816 kN (traccion) | +8.437816 kN | ~9e-15 |
| axial columna sotavento (12) | -48.437816 kN (compresion) | -48.437816 kN | ~1e-15 |
| axial viga (21) | 0 kN | 0 kN | ~1e-12 |
| momento base columna \|Mz_i\| | 114.686552 kN*m | 114.686552 kN*m | ~3e-15 |
| momento top columna \|Mz_j\| | 85.313448 kN*m | 85.313448 kN*m | ~3e-15 |

Equilibrio global: suma de cargas + suma de reacciones = 0 en FX, FY y FZ en
ambos casos (error 0). Ademas, en el marco, la suma de axiales de columnas
recupera la carga vertical aplicada (-40 kN) y el equilibrio rotacional del
nodo 3 (columna + viga) es nulo (~1e-14).

## Contrato de fuerzas locales (validado numericamente)

`ops.eleResponse(tag, "localForce")` retorna 12 componentes en ejes locales:

```
[N_i, Vy_i, Vz_i, T_i, My_i, Mz_i,   N_j, Vy_j, Vz_j, T_j, My_j, Mz_j]
```

Validaciones realizadas sobre este contrato (ver tests):

- Axial: la fuerza interna de tension es `N_j` (y `-N_i`). Evidencia: la
  columna que el vuelco pone en traccion reporta `N_j = +8.44`; la comprimida
  `N_j = -48.44`.
- Momentos: comparados en magnitud; el signo depende de la orientacion del
  elemento. La convencion se fija por dos chequeos cruzados: el momento de
  extremo del voladizo reproduce `P*L = 30` en magnitud, y el equilibrio
  rotacional del nodo 3 del marco suma cero entre `Mz_j` de la columna y
  `My_i` de la viga (+85.313 - 85.313 = 0).
- Corte: `Vy_i = -Vy_j` y `Vz_i = -Vz_j` para elementos sin carga distribuida.

Regla del curso respetada: no se nombra ninguna componente sin haber
confirmado fisicamente que representa (validacion numerica arriba).

## Preparacion defensa individual

- **Los 6 GDL:** cada nodo 3D tiene 3 traslaciones (uX, uY, uZ: GDL 1-3) y 3
  rotaciones (thetaX, thetaY, thetaZ: GDL 4-6). Por eso `ops.model("basic", "-ndm", 3, "-ndf", 6)` y por eso las cargas y reacciones nodales tienen 6 componentes.
- **Que representa geomTransf:** define como se orientan los ejes locales de
  cada elemento a partir del eje x (nodo I -> nodo J) y del vector vecxz, que
  indica hacia donde apunta el plano local x-z. Con vecxz = (0,0,1) una viga
  sobre X queda con local y = Y y local z = Z globales. Nunca usar vecxz
  paralelo al eje del elemento (por eso las columnas usan (0,1,0)).
- **Diferencia local/global:** las cargas `eleLoad`, las rigideces Iy/Iz y
  `localForce` viven en ejes LOCALES del elemento; los desplazamientos
  `nodeDisp`, las cargas `load` y las reacciones `nodeReaction` viven en ejes
  GLOBALES. Confundirlos es la fuente tipica de errores de signo o de Iy/Iz
  intercambiados.
- **Que representa Iy e Iz:** las inercias para flexion alrededor de los ejes
  locales y y z respectivamente (Iy acompana desplazamiento segun local z).
  Para la viga 0.30x0.50 con local z vertical: Iy = b*h^3/12 = 3.125e-3 m^4
  (eje fuerte); Iz = h*b^3/12 = 1.125e-3 m^4. Intercambiarlos cambia el
  desplazamiento 2.78 veces.
- **Que esta resolviendo OpenSees:** ensambla la matriz de rigidez K del
  sistema de elementos, resuelve K u = F para los desplazamientos nodales y de
  ahi recupera reacciones y fuerzas de elemento. En este lab: sistema lineal
  elastico estatico, un paso con LoadControl 1.0.
- **Por que converger no significa estar correcto:** `analyze() == 0` solo
  dice que el problema NUMERICO se resolvio. No valida unidades, ejes
  locales, apoyos, cargas ni conectividad: un modelo con Iy/Iz intercambiados
  o un apoyo equivocado converge perfectamente y da resultados absurdos. Por
  eso existen las verificaciones independientes (equilibrio, soluciones
  analiticas, simetria, orden de magnitud) de este repositorio.

## Estructura

```
data/    casos en JSON (datos separados de la construccion)
src/     model.py builder JSON->OpenSees, analysis.py analisis,
         results.py extraccion, reference.py soluciones independientes,
         verify.py verificaciones, visualize.py figura, run_benchmark.py CLI
tests/   pytest: 9 pruebas end-to-end contra referencias analiticas
results/ JSON de verificacion y figuras
```

## Estado actual

Laboratorio P1L1 completo: ambos casos reproducen con errores a nivel de
precision de maquina (~1e-15), 9/9 pruebas pasan y las salidas JSON + figuras
estan generadas.
