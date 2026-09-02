# P1L1_Grupo4

Pórtico 3D de hormigón armado — Proyecto 1 Grupo 4.

Análisis elástico lineal de un pórtico tridimensional de un piso en OpenSeesPy.
El peso propio de la losa se transfiere a las vigas como carga distribuida
(`eleLoad -beamUniform`), y de estas a las columnas. El modelo completo
se define en un archivo JSON editable.

## Sistema de unidades

SI coherente:

| Magnitud | Unidad |
|---|---|
| Longitud | m |
| Fuerza | kN |
| Tensión / módulo | kN/m² |
| Momento | kN·m |

## Instalación

```powershell
git clone https://github.com/mauricio-lenz/P1L1_Grupo4.git
cd P1L1_Grupo4
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```powershell
.venv\Scripts\Activate.ps1
python -m src.portico_3d                       # usa data/portico_3d.json por defecto
python -m src.portico_3d data/portico_3d.json   # ruta explícita
python -m src.edificio                          # edificio 5 niveles (data/edificio_config.json)
```

Salidas:
- `results/figures/portico_3d.png`: visualización 3D con deformada.
- Impresión en terminal de reacciones, desplazamientos, fuerzas internas y resumen crítico.

## Geometría

Pórtico de un piso con planta rectangular de **3 × 6 m** y altura de piso **3 m**.

```
    8 -------- 7           z = 3 m (techo)
    |          |
    |  VIGAS   |
    |          |
    5 -------- 6
    |          |
    | COLUMNAS |
    |          |
    4 -------- 3           z = 0 m (base)
    |          |           Apoyos empotrados
    1 -------- 2

    X: 0 → 3 m   (vías cortas)
    Y: 0 → 6 m   (vías largas)
```

| Nodo | X [m] | Y [m] | Z [m] |
|---|---|---|---|
| 1 | 0.0 | 0.0 | 0.0 |
| 2 | 3.0 | 0.0 | 0.0 |
| 3 | 3.0 | 6.0 | 0.0 |
| 4 | 0.0 | 6.0 | 0.0 |
| 5 | 0.0 | 0.0 | 3.0 |
| 6 | 3.0 | 0.0 | 3.0 |
| 7 | 3.0 | 6.0 | 3.0 |
| 8 | 0.0 | 6.0 | 3.0 |

## Material — Hormigón H30

| Propiedad | Valor | Fórmula |
|---|---|---|
| f'c | 25 MPa | — |
| Ec | 23 500 000 kN/m² (23.5 GPa) | 4700·√f'c |
| ν | 0.20 | — |
| G | 9 791 667 kN/m² (9.79 GPa) | E / (2·(1+ν)) |
| γ | 25 kN/m³ | — |

## Secciones

| Elemento | b × h [m] | A [m²] | Iy [m⁴] | Iz [m⁴] |
|---|---|---|---|---|
| Columna | 0.30 × 0.30 | 0.0900 | 6.75×10⁻⁴ | 6.75×10⁻⁴ |
| Viga | 0.20 × 0.40 | 0.0800 | 1.067×10⁻³ | 2.667×10⁻⁴ |

**Inercia torsional:**
- Columna: J = 0.1406 · b⁴ = 1.139×10⁻³ m⁴
- Viga: J = 0.196 · b_min³ · b_max = 1.024×10⁻³ m⁴

## Transformaciones geometricas

| Etiqueta | Uso | Vecxz |
|---|---|---|
| 1 | Columnas (eje local x → Z global) | [1, 0, 0] |
| 2 | Vigas en X | [0, 0, 1] |
| 3 | Vigas en Y | [0, 0, 1] |

Las columnas van de base a techo; su eje local x sigue la dirección vertical (Z global).
Las vigas usan vecxz = [0, 0, 1] para que el eje local z apunte hacia arriba.

## Cálculo de cargas: peso propio de la losa → vigas

### Datos de la losa

| Parámetro | Valor |
|---|---|
| Extensión | 3 m (X) × 6 m (Y) |
| Espesor | 0.15 m |
| γ | 25 kN/m³ |
| Peso total | 3 × 6 × 0.15 × 25 = **67.5 kN** |

### Áreas tributarias

La losa se apoya en 4 vigas perimetrales. Cada viga recibe la mitad de la
carga de la losa en su dirección:

```
         Y = 6 m
    4 -------- 3
    |  1.5 m   |
    |←--------→|  (tributario de vigas en Y)
    |          |
    5 -------- 6
         X = 3 m
```

| Dirección | Vigas | Longitud | Ancho tributario | Área tributaria | w [kN/m] |
|---|---|---|---|---|---|
| Cortas (X) | Tags 5, 7 | 3 m | 6 / 2 = 3.0 m | 9.0 m² | 3.0 × 0.15 × 25 = **2.8125** |
| Largas (Y) | Tags 6, 8 | 6 m | 3 / 2 = 1.5 m | 9.0 m² | 1.5 × 0.15 × 25 = **4.21875** |

**Verificación de la carga total aplicada:**

```
2 vigas cortas:  2 × 2.8125 kN/m × 3 m  = 16.875 kN
2 vigas largas:  2 × 4.21875 kN/m × 6 m = 50.625 kN
                                     TOTAL = 67.500 kN  ✓
```

### Aplicación en OpenSeesPy

Las cargas se aplican como carga uniforme en ejes locales mediante `eleLoad`:

```python
# Vigas en X (tags 5, 7): carga vertical en eje local z
ops.eleLoad("-ele", 5, "-type", "-beamUniform", 0, -2.8125)  # wy=0, wz=-2.8125
ops.eleLoad("-ele", 7, "-type", "-beamUniform", 0, -2.8125)

# Vigas en Y (tags 6, 8)
ops.eleLoad("-ele", 6, "-type", "-beamUniform", 0, -4.21875) # wy=0, wz=-4.21875
ops.eleLoad("-ele", 8, "-type", "-beamUniform", 0, -4.21875)
```

El valor negativo en `wz` indica dirección descendente (gravedad).

## Camino de carga

```
  PESO PROPIO DE LA LOSA (67.5 kN)
            |
            v
  CÁLCULO DE ÁREAS TRIBUTARIAS
  w = ancho_tributario × espesor × γ
            |
            v
  CARGA DISTRIBUIDA EN VIGAS (eleLoad -beamUniform)
  vigas cortas: 2.8125 kN/m    vigas largas: 4.21875 kN/m
            |
            v
  VIGAS → cortante Vz + momento flector My
            |
            v
  NODOS ESQUINA (5, 6, 7, 8)
  conexión viga–columna
            |
            v
  COLUMNAS → fuerza axial N + momentos flectores
            |
            v
  APOYOS EMPOTRADOS (nodos 1–4)
  reacciones FZ + momentos
```

## Resultados del análisis

### Reacciones en la base

| Nodo | FX [kN] | FY [kN] | FZ [kN] | MX [kN·m] | MY [kN·m] | MZ [kN·m] |
|---|---|---|---|---|---|---|
| 1 | 0.5873 | 4.5126 | 16.8750 | -4.4872 | 0.5856 | 0.0000 |
| 2 | -0.5873 | 4.5126 | 16.8750 | -4.4872 | -0.5856 | 0.0000 |
| 3 | -0.5873 | -4.5126 | 16.8750 | 4.4872 | -0.5856 | 0.0000 |
| 4 | 0.5873 | -4.5126 | 16.8750 | 4.4872 | 0.5856 | 0.0000 |
| **Suma** | **0.0000** | **0.0000** | **67.5000** | **0.0000** | **0.0000** | **0.0000** |

**Verificación:** ΣFZ = 67.50 kN = peso total de la losa. Equilibrio global ✓

### Desplazamientos del techo (nodos 5–8)

| Nodo | Ux [m] | Uy [m] | Uz [m] |
|---|---|---|---|
| 5 | 4.69×10⁻⁷ | 7.20×10⁻⁶ | -2.39×10⁻⁵ |
| 6 | -4.69×10⁻⁷ | 7.20×10⁻⁶ | -2.39×10⁻⁵ |
| 7 | -4.69×10⁻⁷ | -7.20×10⁻⁶ | -2.39×10⁻⁵ |
| 8 | 4.69×10⁻⁷ | -7.20×10⁻⁶ | -2.39×10⁻⁵ |

La Flecha vertical es uniforme: **Uz = -0.024 mm** (prácticamente nulo para un pórtico rígido).

### Fuerzas internas — vigas (eje local)

| Elemento | Tipo | Vz_i [kN] | Vz_j [kN] | My_i [kN·m] | My_j [kN·m] |
|---|---|---|---|---|---|
| 5 | Viga corta (3 m) | 4.2188 | 4.2188 | -1.1762 | 1.1762 |
| 7 | Viga corta (3 m) | 4.2188 | 4.2188 | -1.1762 | 1.1762 |
| 6 | Viga larga (6 m) | 12.6562 | 12.6563 | -9.0506 | 9.0506 |
| 8 | Viga larga (6 m) | 12.6562 | 12.6562 | -9.0506 | 9.0506 |

**Viga corta (3 m):** corte Vz = 4.22 kN, momento máximo My = 1.18 kN·m.
**Viga larga (6 m):** corte Vz = 12.66 kN, momento máximo My = 9.05 kN·m.

### Fuerzas internas — columnas (eje local)

| Elemento | N_i [kN] | N_j [kN] | Máx |M| [kN·m] |
|---|---|---|---|
| 1 (Col 1→5) | 16.875 | -16.875 | 9.0506 |
| 2 (Col 2→6) | 16.875 | -16.875 | 9.0506 |
| 3 (Col 3→7) | 16.875 | -16.875 | 9.0506 |
| 4 (Col 4→8) | 16.875 | -16.875 | 9.0506 |

Cada columna soporta **N = -16.875 kN** (compresión) = 67.5 / 4.

### Resumen de resultados críticos

| Resultado | Valor |
|---|---|
| **Columnas** | |
| Fuerza axial máxima (compresión) | -16.875 kN |
| Momento flector máximo absoluto | 9.0506 kN·m |
| **Vigas cortas (3 m)** | |
| Momento flector máximo absoluto | 1.1762 kN·m |
| Fuerza de corte máxima absoluta | 4.2188 kN |
| **Vigas largas (6 m)** | |
| Momento flector máximo absoluto | 9.0506 kN·m |
| Fuerza de corte máxima absoluta | 12.6563 kN |

## Datos del modelo (JSON)

Todo el modelo se define en `data/portico_3d.json`:

```json
{
  "material":       { "E": 23500000.0, "nu": 0.20 },
  "secciones":      { "columna": {"b":0.30,"h":0.30}, "viga": {"b":0.20,"h":0.40} },
  "nodos":          { "1": [0,0,0], ..., "8": [0,6,3] },
  "apoyos":         { "1": [1,1,1,1,1,1], ... },
  "geomTransf":     { "columnas": {"tag":1,"vecxz":[1,0,0]}, ... },
  "elementos":      [ { "tag":1, "i":1, "j":5, "seccion":"columna", ... }, ... ]
}
```

Para modificar la geometría, secciones o cargas, basta editar el JSON y volver a ejecutar.

## Edificio institucional 5 niveles (`src/edificio.py`)

Modelo elástico lineal del edificio real **2017_67 (U. de los Andes)**,
extraído de los planos DXF (series 100-103 de estructura). Tiene 1
subterráneo + 4 pisos (altura de piso 3.96 m), grilla de columnas
E,F,G,H,I,I' × 3,2,1 (6×3), columnas P.70×70, vigas V.60×80, muros de
núcleo e=20 cm (wide-column), losas rígidas (`rigidDiaphragm`) y cargas
por áreas tributarias. Incluye el **voladizo al este (eje J)**: viga
cantilever V.60×80 de I' a J (5.0 m, x=58.932 m) en **Piso3 y Piso4** con
losa saliente 1.0 m (fascia x=59.932 m) y parapeto 0.75 m, sin columnas
bajo J (definido en `cargas` del config como `voladizos`).

- Geometría: `data/edificio_config.json` (ejes en m, extraídos del DXF
  a escala 1 u = 1 cm).
- Unidades: SI coherente (m, kN, kN/m²).
- Cargas: `q_G` = peso propio losa (e=0.15 m) + terminaciones
  (5.25 kN/m² pisos, 4.25 kN/m² cubierta).

```text
python -m src.edificio                       # usa data/edificio_config.json
python -m src.edificio data/edificio_config.json   # ruta explícita
```

El modelo genera la salida QA en consola (tablas CSV):

- `# nivel,qG,carga_losa_piso,area_piso,suma_w_X,suma_w_Y`: losa por piso.
- `# verificacion_areas_tributarias`: por piso, X = Y = 363 m² y total = 726.8 m² =
  `area_piso` (los pisos con voladizo suman 96.9 m² más → 823.7 m² en Piso3/Piso4).
- `# reacciones_basales`: fuerza y momento en todos los nodos de la base.
- `# conservacion_carga`: `carga_total_aplicada` ≈ `suma_reacciones_FZ` (diferencia ~0)
  y ΣF<sub>x</sub> = ΣF<sub>y</sub> = 0.
- `# compatibilidad_diafragma`: residuo de cuerpo rígido de cada piso vs nodo
  maestro (debe ser ~0).

Además genera una vista 3D (`results/figures/edificio_3d.png`) y exporta el
modelo completo a JSON en `results/export/` para el viewer/Unity:

- `nodos.json`: `{tag, x, y, z}` por nodo.
- `elementos.json`: `elementTag, tipo (columna/viga/diagonal/muro), n1, n2,
  seccion, material, transf (eje local), L`.
- `diafragmas.json`: por nivel, nodo `master` + lista de `slaves`.
- `apoyos.json`: `{tag, ux, uy, uz, rx, ry, rz}` de cada apoyo (1 = restringido).
- `secciones.json`: secciones tipo y materiales del config.
- `tributarias.json`: por viga, `elementTag`, `w_kN_m`, `asa_x_m`/`asa_y_m` y
  `carga_losa_kN`; más `carga_total_losa_kN` y `carga_puntual_kN`.
- `verificaciones.json`: carga de losa por piso, áreas tributarias,
  conservación de carga, equilibrio global y reacciones basales.

Estos JSON permiten responder en el viewer a "¿qué elementTag tiene?",
"¿qué apoyos tiene?", "¿cuál es su eje local?", "¿qué área tributaria carga
esta viga?" y "¿cuántos kN de losa llegan a ella?".

### Dónde inyectar las coordenadas reales

Todo el edificio se describe en `data/edificio_config.json` (con las
coordenadas/cargas/secciones del proyecto). Para modificarlas se edita
únicamente ese archivo:

| Clave | Qué describe | Qué editar |
|---|---|---|
| `grilla_ejes.X` / `.Y` | coordenadas de los ejes | sustituir los valores por los reales del proyecto (en `orden_x`/`orden_y` se indica el orden de los ejes) |
| `niveles` | altura (elevación Z) de cada nivel | claves `Subterraneo`, `Piso1..4`, `Cubierta` y valor `base` (altura de empotramiento) |
| `materiales` / `secciones_tipo` | módulos, ν, y secciones de vigas/columnas/muros/diagonales | geometrías y propiedades de los elementos |
| `cargas.qG` / `.g` / `.puntuales` | carga de losa por nivel (kN/m²), gravedad y cargas puntuales (peso_kg, tipo `nodo`/`viga`, `posicion`, `factor`) | cargas de diseño |
| `arriostramientos` | frames donde van las diagonales X, patron y rango de niveles | ubicación real del arriostramiento |
| `muros` | muros de cortante (orientación, línea de ejes, rango de niveles) | simetría real del edificio |
| `voladizos` | voladizos (eje J): ejes de apoyo/destino, `x_j_m`, niveles, sección de viga, losa saliente y ejes Y | voladizo al este visto en elevaciones 302/300/303 |

Los nombres de los niveles (`niveles`), ejes (`grilla_ejes`) y los valores de
`qG` deben mantener coherencia entre secciones: el script resuelve los
índices de eje/nivel por nombre.

## Estructura del proyecto

```
P1L1_Grupo4/
  data/
    portico_3d.json              Datos del pórtico 3D
    edificio_config.json         Datos del edificio institucional (grilla, niveles, cargas)
    estructura_simple.json       Datos de la estructura simple (shell)
  src/
    __init__.py
    portico_3d.py                Modelo 3D, análisis y visualización
    edificio.py                  Edificio 5 niveles con muros, diagonales y QA
    simple_analysis.py           Modelo con losa shell (shellMITC4)
  results/
    figures/
      portico_3d.png             Figura 3D del pórtico
      estructura_simple.png      Figura de la estructura simple
      edificio_3d.png            Vista 3D del edificio con deformada
    export/
      nodos.json                 Nodos del edificio (tag, x, y, z)
      elementos.json             Elementos (elementTag, n1/n2, seccion, transf)
      diafragmas.json            Diafragmas rígidos (master + slaves por nivel)
      apoyos.json                Apoyos (GDL restringidos)
      secciones.json             Secciones tipo y materiales
      tributarias.json           Áreas tributarias y carga de losa por viga
      verificaciones.json        Verificaciones (conservación, equilibrio, etc.)
      grilla.json                Ejes/niveles por nombre (para el viewer Unity)
  unity-viewer/                  Proyecto Unity (viewer 3D del edificio)
    Assets/Scripts/              Código C# (loader, geometría, cámara, UI)
    Assets/Editor/               Auto-genera la escena Main al primer import
    Assets/StreamingAssets/json/ Copia de results/export para el viewer
  tools/
    sync_unity_assets.ps1        Copia results/export/*.json al viewer
  requirements.txt
  pytest.ini
  AGENTS.md
  README.md
```

## Viewer Unity (`unity-viewer/`)

Edifica el modelo 3D del edificio 2017_67 a partir de `results/export/*.json`,
coloreado por tipo y con inspección de elementos al hacer clic.

- Colores: columnas rojo, vigas azul, vigas del voladizo (eje J) cian,
  muros naranja, apoyos verde claro.
- Al seleccionar un elemento muestra: `elementTag`, tipo, nivel, orientación,
  sección, material, longitud `L` y `w` (kN/m) de carga de losa.
- Cámara: botón derecho = orbitar, scroll = zoom, botón central = panear,
  Escape deselecciona.

Abrir: abrir `unity-viewer/` desde Unity Hub (Unity 6.3.23f1 LTS). El modelo
se construye automáticamente al abrir la escena `Assets/Scenes/Main.unity` (no
requiere dar Play para verlo; también menú `Edificio -> Reconstruir modelo
visible`). Para inspeccionar elementos (click) y orbitar la cámara hay que dar
Play. Para refrescar los datos:

```powershell
python -m src.edificio    # regenera results/export
.\tools\sync_unity_assets.ps1
```

## Entorno

- Windows 11
- Python 3.12
- OpenSeesPy 3.8.0
