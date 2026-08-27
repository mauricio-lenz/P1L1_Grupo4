# Informe — Proyecto 1, Grupo 4
## Análisis estático lineal de un pórtico 3D de hormigón armado con OpenSeesPy

---

## 1. Objetivo

Modelar y analizar un pórtico tridimensional de un piso de hormigón armado
mediante el programa OpenSeesPy, aplicando el peso propio de la losa como
carga distribuida sobre las vigas y comprobando el camino de cargas:
**losa → vigas → columnas → apoyos**.

El trabajo incluye la verificación del equilibrio global (suma de cargas
igual a suma de reacciones) y la validación de desplazamientos y de
esfuerzos internos en los elementos.

---

## 2. Modelo estructural

### 2.1 Geometría

El pórtico tiene un piso, una planta rectangular de **3 × 6 m** y altura de
piso de **3 m**. Está compuesto por 4 columnas y 4 vigas perimetrales.

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

- Nodos 1–4: base empotrada (Z = 0).
- Nodos 5–8: techo (Z = 3 m).

### 2.2 Material

Hormigón H30, comportamiento elástico lineal.

| Propiedad | Valor |
|---|---|
| Resistencia f'c | 25 MPa |
| Módulo de elasticidad Ec | 4700·√f'c = 23 500 000 kN/m² |
| Coeficiente de Poisson ν | 0.20 |
| Módulo de corte G | E / (2·(1+ν)) = 9.79 GPa |
| Peso específico γ | 25 kN/m³ |

### 2.3 Secciones

| Elemento | b × h [m] | A [m²] | Iy [m⁴] | Iz [m⁴] |
|---|---|---|---|---|
| Columna | 0.30 × 0.30 | 0.090 | 6.75×10⁻⁴ | 6.75×10⁻⁴ |
| Viga | 0.20 × 0.40 | 0.080 | 1.07×10⁻³ | 2.67×10⁻⁴ |

### 2.4 Elementos

Todos los elementos se modelan como `elasticBeamColumn` (6 grados de
libertad por nodo):

- 4 columnas (nodos base → techo).
- 4 vigas: 2 cortas de 3 m (en X) y 2 largas de 6 m (en Y).

---

## 3. Cálculo de cargas: peso propio de la losa

### 3.1 Datos de la losa

- Extensión: 3 m × 6 m
- Espesor: 0.15 m
- Peso específico: γ = 25 kN/m³
- **Peso total = 3 × 6 × 0.15 × 25 = 67.5 kN**

### 3.2 Método de áreas tributarias

La losa se apoya en las 4 vigas perimetrales. Cada viga recibe la mitad de
la carga de la losa en la dirección en la que trabaja.

| Dirección | Vigas | Longitud | Ancho tributario | Carga uniforme w |
|---|---|---|---|---|
| Cortas (X) | 5 y 7 | 3 m | 6/2 = 3.0 m | 3.0 × 0.15 × 25 = 2.8125 kN/m |
| Largas (Y) | 6 y 8 | 6 m | 3/2 = 1.5 m | 1.5 × 0.15 × 25 = 4.21875 kN/m |

### 3.3 Verificación de la carga total

```
2 vigas cortas:  2 × 2.8125 × 3  = 16.875 kN
2 vigas largas:  2 × 4.21875 × 6 = 50.625 kN
                             TOTAL = 67.500 kN  ✓
```

Coincide con el peso total de la losa. Esta carga se aplica en OpenSeesPy
mediante el comando `eleLoad -beamUniform` sobre cada viga.

---

## 4. Análisis

El análisis es **estático lineal** con los siguientes componentes de OpenSeesPy:

- `constraints Plain`, `numberer RCM`, `system BandGeneral`
- `algorithm Linear`, `integrator LoadControl`, `analysis Static`
- Luego de resolver, se llama a `reactions()` para obtener las reacciones
  de los apoyos.

---

## 5. Verificaciones y resultados

### 5.1 Suma de cargas y suma de reacciones (equilibrio global)

| Concepto | Valor |
|---|---|
| Carga total aplicada (peso losa) | −67.5000 kN |
| Suma de reacciones FZ (apoyos) | 67.5000 kN |
| Diferencia | 0.000000 kN |

**Estado: CUMPLE** — se verifica el equilibrio vertical global.

### 5.2 Suma de reacciones horizontales

Se verifica también que ΣFX y ΣFY sean nulas (no hay cargas horizontales).

### 5.3 Desplazamiento de un nodo

Desplazamientos del nivel techo (nodos 5–8):

| Nodo | Ux [m] | Uy [m] | Uz [m] |
|---|---|---|---|
| 5 | 4.69×10⁻⁷ | 7.20×10⁻⁶ | −2.39×10⁻⁵ |
| 6 | −4.69×10⁻⁷ | 7.20×10⁻⁶ | −2.39×10⁻⁵ |
| 7 | −4.69×10⁻⁷ | −7.20×10⁻⁶ | −2.39×10⁻⁵ |
| 8 | 4.69×10⁻⁷ | −7.20×10⁻⁶ | −2.39×10⁻⁵ |

Flecha vertical máxima: **Uz ≈ −0.024 mm** (prácticamente despreciable,
propio de un pórtico rígido sin losa flectando).

### 5.4 Fuerza axial en un elemento

| Elemento | N [kN] |
|---|---|
| Columna 1 | 16.875 |
| Columna 2 | 16.875 |
| Columna 3 | 16.875 |
| Columna 4 | 16.875 |

**Verificación:** N esperado = 67.5 / 4 = 16.875 kN ✓ (cada columna soporta
la cuarta parte del peso total en compresión).

### 5.5 Momento en extremo de un elemento

| Elemento | My nodo i [kN·m] | My nodo j [kN·m] |
|---|---|---|
| Columna 1 | −0.586 | −1.176 |
| Columna 2 | 0.586 | 1.176 |
| Columna 3 | 0.586 | 1.176 |
| Columna 4 | −0.586 | −1.176 |

Momento flector máximo absoluto en columnas: **9.05 kN·m**.

### 5.6 Resumen de resultados críticos

| Resultado | Valor |
|---|---|
| Fuerza axial máxima en columnas (compresión) | −16.875 kN |
| Momento máximo en columnas | 9.05 kN·m |
| Corte en vigas cortas (3 m) | 4.22 kN |
| Momento en vigas cortas | 1.18 kN·m |
| Corte en vigas largas (6 m) | 12.66 kN |
| Momento en vigas largas | 9.05 kN·m |

---

## 6. Camino de cargas (conclusión)

El análisis reproduce correctamente el flujo del peso propio:

```
Peso losa (67.5 kN)
      ↓
Áreas tributarias → carga distribuida en vigas
      ↓
Vigas → cortante y momento flector
      ↓
Columnas → fuerza axial + momentos
      ↓
Apoyos → reacciones (ΣFZ = 67.5 kN)
```

Se confirma el camino **losa → viga → columna → apoyo**, con equilibrio
global verificado.

---

## 7. Archivos del proyecto

| Archivo | Descripción |
|---|---|
| `data/portico_3d.json` | Datos del modelo (material, secciones, nodos, elementos, cargas) |
| `src/portico_3d.py` | Modelo, análisis, verificaciones y visualización 3D |
| `results/figures/portico_3d.png` | Figura 3D del pórtico con deformada |
| `README.md` | Documentación completa del proyecto |

**Ejecución:**

```powershell
.venv\Scripts\Activate.ps1
python -m src.portico_3d
```

**Entorno:** Windows 11 · Python 3.12 · OpenSeesPy 3.8.0
