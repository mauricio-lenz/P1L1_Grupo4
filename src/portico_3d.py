"""
Portico 3D simple (1 piso, 1 vano) - Proyecto 1 Grupo 4
Analisis estatico lineal con cargas distribuidas en vigas
que representan el peso de una losa.

Geometria:
  4 columnas (0.30x0.30 m), 4 vigas (0.20x0.40 m)
  Planta 3x6 m, altura 3 m

Cargas:
  Peso de losa distribuido sobre vigas via eleLoad -beamUniform
  Vigas cortas (3m): w = -2.8125 kN/m
  Vigas largas (6m): w = -4.21875 kN/m

Uso:
    python -m src.portico_3d
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openseespy.opensees as ops
from pathlib import Path


# =====================================================================
# 1. DEFINICION DEL MODELO Y GEOMETRIA
# =====================================================================

def construir_modelo():
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    # -----------------------------------------------------------------
    # Material
    # -----------------------------------------------------------------
    E = 23_500_000.0   # kN/m2
    nu = 0.20
    G = E / (2.0 * (1.0 + nu))

    ops.uniaxialMaterial("Elastic", 1, E)

    # -----------------------------------------------------------------
    # Propiedades de secciones
    # -----------------------------------------------------------------
    # Columna 0.30 x 0.30 m
    b_c, h_c = 0.30, 0.30
    A_c  = b_c * h_c
    Iy_c = b_c * h_c**3 / 12.0
    Iz_c = h_c * b_c**3 / 12.0
    J_c  = 0.1406 * b_c**4

    # Viga 0.20 x 0.40 m
    b_v, h_v = 0.20, 0.40
    A_v  = b_v * h_v
    Iy_v = b_v * h_v**3 / 12.0
    Iz_v = h_v * b_v**3 / 12.0
    J_v  = 0.196 * min(b_v, h_v)**3 * max(b_v, h_v)

    # -----------------------------------------------------------------
    # Nodos
    # -----------------------------------------------------------------
    # Base (z=0)
    ops.node(1, 0.0, 0.0, 0.0)
    ops.node(2, 3.0, 0.0, 0.0)
    ops.node(3, 3.0, 6.0, 0.0)
    ops.node(4, 0.0, 6.0, 0.0)

    # Techo / Losa (z=3)
    ops.node(5, 0.0, 0.0, 3.0)
    ops.node(6, 3.0, 0.0, 3.0)
    ops.node(7, 3.0, 6.0, 3.0)
    ops.node(8, 0.0, 6.0, 3.0)

    # -----------------------------------------------------------------
    # Apoyos (empotrados)
    # -----------------------------------------------------------------
    for tag in [1, 2, 3, 4]:
        ops.fix(tag, 1, 1, 1, 1, 1, 1)

    # -----------------------------------------------------------------
    # Transformaciones geometricas
    # -----------------------------------------------------------------
    # Columnas (eje local x a lo largo de Z global)
    ops.geomTransf("Linear", 1, 1, 0, 0)

    # Vigas en X (eje local x a lo largo de X global)
    ops.geomTransf("Linear", 2, 0, 0, 1)

    # Vigas en Y (eje local x a lo largo de Y global)
    ops.geomTransf("Linear", 3, 0, 0, 1)

    # -----------------------------------------------------------------
    # Elementos
    # -----------------------------------------------------------------
    # Columnas (tags 1-4)
    col_params = [A_c, E, G, J_c, Iy_c, Iz_c]
    ops.element("elasticBeamColumn", 1, 1, 5, *col_params, 1)
    ops.element("elasticBeamColumn", 2, 2, 6, *col_params, 1)
    ops.element("elasticBeamColumn", 3, 3, 7, *col_params, 1)
    ops.element("elasticBeamColumn", 4, 4, 8, *col_params, 1)

    # Vigas (tags 5-8)
    vig_params = [A_v, E, G, J_v, Iy_v, Iz_v]
    ops.element("elasticBeamColumn", 5, 5, 6, *vig_params, 2)  # corta X
    ops.element("elasticBeamColumn", 6, 6, 7, *vig_params, 3)  # larga Y
    ops.element("elasticBeamColumn", 7, 7, 8, *vig_params, 2)  # corta X
    ops.element("elasticBeamColumn", 8, 8, 5, *vig_params, 3)  # larga Y

    return {"E": E, "G": G, "A_c": A_c, "Iy_c": Iy_c, "Iz_c": Iz_c, "J_c": J_c,
            "A_v": A_v, "Iy_v": Iy_v, "Iz_v": Iz_v, "J_v": J_v}


# =====================================================================
# 4. CARGAS DISTRIBUIDAS (peso de losa sobre vigas)
# =====================================================================

def aplicar_cargas():
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    w_corta = -2.8125    # kN/m  (vigas tags 5 y 7)
    w_larga = -4.21875   # kN/m  (vigas tags 6 y 8)

    # eleLoad -beamUniform: carga en ejes locales wy, wz
    # Con geomTransf 2 y 3, local z apunta hacia arriba (global Z)
    # por lo que carga gravitacional va en wz (negativo = hacia abajo)
    ops.eleLoad("-ele", 5, "-type", "-beamUniform", 0, w_corta)
    ops.eleLoad("-ele", 7, "-type", "-beamUniform", 0, w_corta)
    ops.eleLoad("-ele", 6, "-type", "-beamUniform", 0, w_larga)
    ops.eleLoad("-ele", 8, "-type", "-beamUniform", 0, w_larga)

    total = (2 * w_corta * 3.0) + (2 * w_larga * 6.0)
    return total


# =====================================================================
# 5. ANALISIS
# =====================================================================

def analizar():
    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")
    ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError("El analisis fallo")
    ops.reactions()


# =====================================================================
# RESULTADOS DETALLADOS
# =====================================================================

def imprimir_resultados():
    SEP = "=" * 78

    # ── REACCIONES BASE ─────────────────────────────────────────────
    print(f"\n{SEP}")
    print("REACCIONES EN LA BASE (Nodos 1-4, empotrados)")
    print(SEP)
    print(f"{'Nodo':>6} {'FX [kN]':>12} {'FY [kN]':>12} {'FZ [kN]':>12}"
          f" {'MX [kN*m]':>12} {'MY [kN*m]':>12} {'MZ [kN*m]':>12}")
    print("-" * 78)

    sum_fz = 0.0
    for tag in [1, 2, 3, 4]:
        r = ops.nodeReaction(tag)
        sum_fz += r[2]
        print(f"{tag:>6} {r[0]:>12.4f} {r[1]:>12.4f} {r[2]:>12.4f}"
              f" {r[3]:>12.4f} {r[4]:>12.4f} {r[5]:>12.4f}")

    print("-" * 78)
    print(f"  Suma FZ = {sum_fz:.4f} kN")

    # ── DESPLAZAMIENTOS NODALES ─────────────────────────────────────
    print(f"\n{SEP}")
    print("DESPLAZAMIENTOS - NIVEL TECHO (Nodos 5-8)")
    print(SEP)
    print(f"{'Nodo':>6} {'Ux [m]':>14} {'Uy [m]':>14} {'Uz [m]':>14}"
          f" {'Rx [rad]':>14} {'Ry [rad]':>14} {'Rz [rad]':>14}")
    print("-" * 86)

    for tag in [5, 6, 7, 8]:
        d = ops.nodeDisp(tag)
        print(f"{tag:>6} {d[0]:>14.6e} {d[1]:>14.6e} {d[2]:>14.6e}"
              f" {d[3]:>14.6e} {d[4]:>14.6e} {d[5]:>14.6e}")

    # ── FUERZAS INTERNAS DE TODOS LOS ELEMENTOS ─────────────────────
    print(f"\n{SEP}")
    print("FUERZAS INTERNAS - ELEMENTOS (eje local)")
    print(SEP)

    nombres = {
        1: "Col 1-5", 2: "Col 2-6", 3: "Col 3-7", 4: "Col 4-8",
        5: "Viga 5-6 (corta)", 6: "Viga 6-7 (larga)",
        7: "Viga 7-8 (corta)", 8: "Viga 8-5 (larga)",
    }

    for tag in range(1, 9):
        resp = ops.eleResponse(tag, "localForce")
        ni, nj = ops.eleNodes(tag)
        nombre = nombres[tag]
        print(f"\n  Elemento {tag}: {nombre}  (Nodos {ni} -> {nj})")
        print(f"    Nodo i:  N={resp[0]:>10.4f}  Vy={resp[1]:>10.4f}"
              f"  Vz={resp[2]:>10.4f}  T={resp[3]:>10.4f}"
              f"  My={resp[4]:>10.4f}  Mz={resp[5]:>10.4f}")
        print(f"    Nodo j:  N={resp[6]:>10.4f}  Vy={resp[7]:>10.4f}"
              f"  Vz={resp[8]:>10.4f}  T={resp[9]:>10.4f}"
              f"  My={resp[10]:>10.4f}  Mz={resp[11]:>10.4f}")

    return _resumen_criticos()


def _resumen_criticos():
    SEP = "=" * 78

    # Extraer todas las fuerzas
    datos = {}
    for tag in range(1, 9):
        resp = ops.eleResponse(tag, "localForce")
        datos[tag] = resp

    # ── COLUMNAS (tags 1-4) ─────────────────────────────────────────
    N_col_max = 0.0
    M_col_max = 0.0
    for tag in [1, 2, 3, 4]:
        r = datos[tag]
        N = min(r[0], r[6])
        M = max(abs(r[4]), abs(r[5]), abs(r[10]), abs(r[11]))
        if abs(N) > abs(N_col_max):
            N_col_max = N
        if M > M_col_max:
            M_col_max = M

    # ── VIGAS CORTAS (tags 5, 7) ────────────────────────────────────
    M_vc_max = 0.0
    V_vc_max = 0.0
    for tag in [5, 7]:
        r = datos[tag]
        M = max(abs(r[4]), abs(r[5]), abs(r[10]), abs(r[11]))
        V = max(abs(r[1]), abs(r[2]), abs(r[7]), abs(r[8]))
        if M > M_vc_max:
            M_vc_max = M
        if V > V_vc_max:
            V_vc_max = V

    # ── VIGAS LARGAS (tags 6, 8) ────────────────────────────────────
    M_vl_max = 0.0
    V_vl_max = 0.0
    for tag in [6, 8]:
        r = datos[tag]
        M = max(abs(r[4]), abs(r[5]), abs(r[10]), abs(r[11]))
        V = max(abs(r[1]), abs(r[2]), abs(r[7]), abs(r[8]))
        if M > M_vl_max:
            M_vl_max = M
        if V > V_vl_max:
            V_vl_max = V

    print(f"\n{SEP}")
    print("RESUMEN DE RESULTADOS CRITICOS")
    print(SEP)

    print("\n  COLUMNAS:")
    print(f"    Fuerza axial max (compresion):  {N_col_max:>10.4f} kN")
    print(f"    Momento flector max absoluto:   {M_col_max:>10.4f} kN*m")

    print("\n  VIGAS CORTAS (3 m):")
    print(f"    Momento flector max absoluto:   {M_vc_max:>10.4f} kN*m")
    print(f"    Fuerza de corte max absoluta:   {V_vc_max:>10.4f} kN")

    print("\n  VIGAS LARGAS (6 m):")
    print(f"    Momento flector max absoluto:   {M_vl_max:>10.4f} kN*m")
    print(f"    Fuerza de corte max absoluta:   {V_vl_max:>10.4f} kN")

    print(f"\n{'=' * 78}")
    print("Analisis completado exitosamente.")
    print(f"{'=' * 78}\n")


# =====================================================================
# VISUALIZACION 3D
# =====================================================================

def visualizar(ruta_salida="results/figures/portico_3d.png"):
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(projection="3d")

    elementos = [
        (1, 1, 5), (2, 2, 6), (3, 3, 7), (4, 4, 8),
        (5, 5, 6), (6, 6, 7), (7, 7, 8), (8, 8, 5),
    ]

    def _coord(tag):
        return np.array([ops.nodeCoord(tag, c + 1) for c in range(3)])

    def _disp(tag):
        return np.array(ops.nodeDisp(tag)[:3])

    max_d = max(np.linalg.norm(_disp(t)) for t in range(1, 9))
    escala = 0.3 / max_d if max_d > 1e-10 else 0.0

    for tag_e, ni, nj in elementos:
        p0 = _coord(ni)
        p1 = _coord(nj)
        es_col = tag_e <= 4
        color = "tab:red" if es_col else "tab:blue"

        ax.plot(*zip(p0, p1), color=color, lw=3, alpha=0.7)

        if escala > 0:
            d0 = _disp(ni)
            d1 = _disp(nj)
            ax.plot(*zip(p0 + escala * d0, p1 + escala * d1),
                    color=color, lw=2, ls="--", alpha=0.5)

    for tag in range(1, 9):
        p = _coord(tag)
        ax.scatter(*p, color="k", s=30, zorder=5)
        ax.text(p[0], p[1], p[2] + 0.15, str(tag),
                fontsize=11, weight="bold", ha="center")

    for tag in [1, 2, 3, 4]:
        p = _coord(tag)
        ax.scatter(*p, marker="s", color="purple", s=120,
                   depthshade=False, zorder=6)

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")
    ax.set_title(
        "Portico 3D - Proyecto 1 Grupo 4\n"
        "Columnas (rojo) | Vigas (azul) | Apoyos (morado)\n"
        + (f"Deformada escala x{escala:.0f}" if escala > 0 else ""),
    )

    manejadores = [
        plt.Line2D([0], [0], color="tab:red", lw=3),
        plt.Line2D([0], [0], color="tab:blue", lw=3),
        plt.Line2D([0], [0], color="gray", lw=2, ls="--"),
        plt.Line2D([0], [0], marker="s", color="purple", lw=0, markersize=8),
    ]
    ax.legend(manejadores, ["Columnas", "Vigas", "Deformada", "Apoyos"],
              loc="upper left", fontsize=9)

    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=200)
    plt.close(fig)
    print(f"Figura guardada: {ruta_salida}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("=" * 78)
    print("PORTICO 3D - ANALISIS ESTATICO LINEAL")
    print("Proyecto 1 Grupo 4")
    print("=" * 78)

    print("\n[1] Construyendo modelo...")
    props = construir_modelo()
    print("    8 nodos, 8 elementos (4 columnas + 4 vigas)")

    print("\n[2] Aplicando cargas distribuidas (peso de losa)...")
    total = aplicar_cargas()
    print(f"    Carga total aplicada: {total:.4f} kN")

    print("\n[3] Ejecutando analisis...")
    analizar()
    print("    Analisis completado.")

    print("\n[4] Extrayendo resultados...")
    imprimir_resultados()

    print("[5] Generando visualizacion 3D...")
    visualizar()


if __name__ == "__main__":
    main()
