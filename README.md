# P1L1_Grupo4

Estructura simple con losa maciza - Proyecto 1 Grupo 4.

Analisis elastico lineal de una estructura de hormigon armado en OpenSeesPy.
La losa se modela con elementos shell (shellMITC4) para capturar la
transferencia real de esfuerzos del peso propio de la losa a las vigas
y de estas a las columnas.

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
python -m src.simple_analysis
```

Salidas:
- `results/figures/estructura_simple.png`: geometria, deformada y apoyos.
- Impresion en terminal de desplazamientos, reacciones, fuerzas de vigas,
  fuerzas de columnas y fuerzas resultantes de la losa.

## Modelo estructural

### Geometria

Planta cuadrada de 4 m x 4 m, altura de piso 3 m.

```
    8 -------- 7
    |          |
    |   LOSA   |
    |  (shell) |
    |          |
    5 -------- 6
    |          |
    | VIGAS    |
    | (4 lados)|
    |          |
    4 -------- 3    Nodos 1-4: base (z=0)
    |          |    Nodos 5-8: nivel losa (z=3m)
    1 -------- 2
```

### Materiales

Hormigon H30:

| Propiedad | Valor |
|---|---|
| f'c | 25 MPa |
| Ec | 4700 * sqrt(f'c) = 23.5 GPa |
| nu | 0.20 |
| G | E / (2*(1+nu)) = 9.79 GPa |
| gamma | 25 kN/m3 |

### Secciones

| Elemento | b x h [m] | A [m2] | Iy [m4] | Iz [m4] |
|---|---|---|---|---|
| Columna | 0.30 x 0.30 | 0.0900 | 6.75e-4 | 6.75e-4 |
| Viga | 0.20 x 0.40 | 0.0800 | 1.07e-3 | 2.67e-4 |
| Losa (espesor) | - | - | - | t = 0.15 m |

### Elementos

| Tipo | Cantidad | Elemento OpenSees | Descripcion |
|---|---|---|---|
| Columnas | 4 | elasticBeamColumn | De base (z=0) a losa (z=3m) |
| Vigas | 16 | elasticBeamColumn | 4 lados x 4 tramos (1 m c/u) |
| Losa | 16 | shellMITC4 | Malla 4x4, 1 panel de 1m x 1m |

Las vigas se dividen en 4 tramos de 1 m para compartir nodos con la malla
de la losa. Esto permite la transferencia de esfuerzos a traves de nodos
compartidos entre shell y viga.

## Transferencia de esfuerzos: peso propio de la losa

### Objeto

Demonstrar como el peso propio de una losa maciza se transfiere
progresivamente a los elementos que la soportan:

```
PESO PROPIO DE LA LOSA
        |
        v
  ELEMENTOS SHELL (shellMITC4)
  distribuyen esfuerzos por stiffness
        |
        v
  NODOS COMPARTIDOS (perimetro)
  la losa transfiere carga a las vigas
        |
        v
  VIGAS DE PERIMETRO (16 tramos)
  reciben carga de corte y momento flector
        |
        v
  NODOS ESQUINA (5, 6, 7, 8)
  punto de conexion viga-columna
        |
        v
  COLUMNAS (4)
  esfuerzo axial + momento por eccentricidad
        |
        v
  APOYOS (reacciones)
```

### Modelo de la losa con elementos shell

La losa se modela con 16 elementos `shellMITC4` (malla 4x4). Cada elemento
tiene4 nodos y un punto de integracion. El material se define con:

```python
ops.section("ElasticMembranePlateSection", secTag, E, nu, espesor, rho)
```

El shellMITC4 captura tanto el comportamiento de membrana (esfuerzos Nxx, Nyy,
Nxy) como de flexion (momentos Mxx, Myy, Mxy) y cortante (Vxz, Vyz).

### Carga: peso propio como cargas nodales equivalentes

El peso propio de la losa se aplica como cargas nodales usando el metodo de
areas tributarias. Cada nodo recibe una carga proporcional al area que
representa:

```
Nodo interior (9 nodos):   area = dx * dy = 1.0 m2
Nodo borde (12 nodos):     area = dx * dy/2 = 0.5 m2  (o dy * dx/2)
Nodo esquina (4 nodos):    area = dx/2 * dy/2 = 0.25 m2

Carga por nodo = area_tributaria * espesor * gamma
```

| Tipo de nodo | Cantidad | Area [m2] | Carga [kN] |
|---|---|---|---|
| Interior | 9 | 1.00 | 3.75 |
| Borde | 12 | 0.50 | 1.875 |
| Esquina | 4 | 0.25 | 0.9375 |
| **Total** | **25** | **16.0** | **60.0** |

Verificacion: 4x4 m x 0.15 m x 25 kN/m3 = 60 kN.

### Mecanismo de transferencia

1. **Los shell distribuyen la carga**: Las cargas nodales aplicadas en los
   nodos interiores se transfieren a traves de la rigidez del shell hacia
   los nodos del perimetro.

2. **Nodos compartidos**: Los nodos del perimetro de la losa (5, 6, 7, 8
   en las esquinas y 101-121 en los bordes) son compartidos con los
   elementos de viga. La carga se transfiere automaticamente a traves de
   la connectivity del modelo.

3. **Las vigas reciben la carga**: Cada tramo de viga recibe carga de corte
   (Vz) y momento flector (Mz) de la losa. Los tramos cercanos a las
   esquinas (conectados a las columnas) reciben mayor carga.

4. **Las columnas soportan todo**: Las reacciones verticales en los apoyos
   suman exactamente 60 kN, verificando el equilibrio global.

### Resultados del analisis

| Resultado | Valor | Interpretacion |
|---|---|---|
| Uz max (centro losa) | 0.83 mm | Flecha de la losa bajo peso propio |
| Reaccion FZ por columna | 15.0 kN | 60 kN / 4 columnas = 15 kN |
| Reaccion FX, FY | +/-2.13 kN | Accion membrana de la losa |
| Vz en vigas (esquina) | 2.99 kN | Corte transferido de losa a viga |
| Mz en columnas | 2.12 kN*m | Momento por eccentricidad de vigas |
| N en columnas | 15.0 kN | Compresion axial |
| Fuerzas en losa | Nxx, Mxx... | Esfuerzos resultantes internos |

### Diferencia con modelo sin shell

En un modelo donde la carga se aplica directamente a los nodos de columna
(sin elementos shell), las vigas tienen fuerza cero porque la carga va
directamente de los nodos a las columnas. Con shellMITC4, la carga se
transfiere a traves de la losa estructural, reproduciendo el camino de
carga real.

| Concepto | Modelo sin shell | Modelo con shell |
|---|---|---|
| Fuerza en vigas | 0 kN | ~3 kN (corte), momento flector |
| Momento en columnas | 0 kN*m | 2.12 kN*m |
| Reacciones horizontales | 0 kN | 2.13 kN (membrana) |
| Flecha de losa | N/A | 0.83 mm |
| Camino de carga | Carga -> columna | Losa -> viga -> columna |

## Estructura del proyecto

```
P1L1_Grupo4/
  data/
    estructura_simple.json     Datos de la estructura (material, secciones, nodos)
  src/
    __init__.py
    simple_analysis.py         Modelo, analisis, resultados y visualizacion
  results/
    figures/
      estructura_simple.png    Figura 3D de la estructura
  requirements.txt
  pytest.ini
  AGENTS.md
  README.md
```

## Sistema operativo y Python

- Windows 11
- Python 3.12
- OpenSeesPy 3.8.0
