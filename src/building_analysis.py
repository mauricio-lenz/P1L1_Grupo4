"""
Modelo 3D del Edificio - Proyecto 1 Grupo 4
Analisis elastico lineal con OpenSeesPy

Unidades: m, kN, kN/m2, kN*m

Estructura:
- 6 columnas cuadradas 70x70 cm en 3 ejes X x 2 ejes Y
- Vigas rectangulares 60x80 cm en direcciones X e Y
- 5 niveles: base (Z=0), sub1 (Z=3.96), p1 (Z=7.92),
  p2 (Z=11.88), p3 (Z=15.84), p4 (Z=19.80)
- Diafragmas rigidos en cada nivel suspendido
- Carga: peso propio de losas (0.15 m, gamma = 25 kN/m3)
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openseespy.opensees as ops


# =====================================================================
# GEOMETRIA (convertida de cm a m)
# =====================================================================

EJES_X = [0.0, 8.90, 16.15]
EJES_Y = [0.0, 5.00]
NIVELES = [
    (0.00, "base"),
    (3.96, "sub1"),
    (7.92, "piso1"),
    (11.88, "piso2"),
    (15.84, "piso3"),
    (19.80, "piso4"),
]


# =====================================================================
# MATERIAL: H30 (f'c = 25 MPa)
# =====================================================================

FC = 25.0
EC = 4700.0 * np.sqrt(FC) * 1e3
NU = 0.20
GC = EC / (2.0 * (1.0 + NU))
GAMMA = 25.0


# =====================================================================
# SECCIONES
# =====================================================================

COL_A = 0.70 * 0.70
COL_IY = 0.70 * 0.70**3 / 12.0
COL_IZ = 0.70 * 0.70**3 / 12.0
COL_J = 0.1406 * 0.70**4

VIG_A = 0.60 * 0.80
VIG_IY = 0.60 * 0.80**3 / 12.0
VIG_IZ = 0.80 * 0.60**3 / 12.0
VIG_J = 0.196 * 0.60**3 * 0.80

ESP_LOSA = 0.15


# =====================================================================
# Helpers
# =====================================================================

def _tag(iz, ci):
    return iz * 100 + ci + 1


def _col_xy(ci):
    return EJES_X[ci % 3], EJES_Y[ci // 3]


# =====================================================================
# CONSTRUCCION DEL MODELO
# =====================================================================

def build():
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    for iz, (z, _) in enumerate(NIVELES):
        for ci in range(6):
            x, y = _col_xy(ci)
            ops.node(_tag(iz, ci), x, y, z)

    for ci in range(6):
        ops.fix(_tag(0, ci), 1, 1, 1, 1, 1, 1)

    ops.geomTransf("Linear", 1, 0, 1, 0)
    ops.geomTransf("Linear", 2, 0, 0, 1)
    ops.geomTransf("Linear", 3, 0, 0, 1)

    ele_tag = 1
    col_tags = []
    viga_x_tags = []
    viga_y_tags = []

    for iz in range(len(NIVELES) - 1):
        for ci in range(6):
            ops.element(
                "elasticBeamColumn", ele_tag,
                _tag(iz, ci), _tag(iz + 1, ci),
                COL_A, EC, GC, COL_J, COL_IY, COL_IZ, 1,
            )
            col_tags.append(ele_tag)
            ele_tag += 1

    for iz in range(1, len(NIVELES)):
        for c1, c2 in [(0, 1), (1, 2), (3, 4), (4, 5)]:
            ops.element(
                "elasticBeamColumn", ele_tag,
                _tag(iz, c1), _tag(iz, c2),
                VIG_A, EC, GC, VIG_J, VIG_IY, VIG_IZ, 2,
            )
            viga_x_tags.append(ele_tag)
            ele_tag += 1

    for iz in range(1, len(NIVELES)):
        for ci in [0, 1, 2]:
            ops.element(
                "elasticBeamColumn", ele_tag,
                _tag(iz, ci), _tag(iz, ci + 3),
                VIG_A, EC, GC, VIG_J, VIG_IY, VIG_IZ, 3,
            )
            viga_y_tags.append(ele_tag)
            ele_tag += 1

    for iz in range(1, len(NIVELES)):
        master = _tag(iz, 4)
        slaves = [_tag(iz, ci) for ci in range(6) if ci != 4]
        ops.rigidDiaphragm(3, master, *slaves)

    return col_tags, viga_x_tags, viga_y_tags


# =====================================================================
# CARGAS: PESO PROPIO DE LOSAS
# =====================================================================

def apply_loads():
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    loads = {}

    def _add(tag, fx, fy, fz):
        loads.setdefault(tag, [0.0, 0.0, 0.0])
        loads[tag][0] += fx
        loads[tag][1] += fy
        loads[tag][2] += fz

    xb = [0.0, 4.45, 12.525, 16.15]
    yb = [0.0, 2.5, 5.0]

    for iz in range(1, len(NIVELES)):
        for ci in range(6):
            ix = ci % 3
            iy = ci // 3
            area = (xb[ix + 1] - xb[ix]) * (yb[iy + 1] - yb[iy])
            W = area * ESP_LOSA * GAMMA
            _add(_tag(iz, ci), 0, 0, -W)

    for tag, fxyz in loads.items():
        ops.load(tag, *fxyz, 0.0, 0.0, 0.0)

    total = sum(f[2] for f in loads.values())
    return loads, total


# =====================================================================
# ANALISIS
# =====================================================================

def analyze():
    ops.constraints("Transformation")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")
    ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError("El analisis fallo")
    ops.reactions()
    return True


# =====================================================================
# RESULTADOS
# =====================================================================

def print_results(total_carga):
    print("\n" + "=" * 72)
    print("DESPLAZAMIENTOS NODALES (m, rad)")
    print("=" * 72)
    fmt = "{:>6} {:>8} {:>12} {:>12} {:>12}"
    print(fmt.format("Nodo", "Nivel", "Ux [m]", "Uy [m]", "Uz [m]"))
    print("-" * 72)

    max_uz_nivel = {}
    for iz, (z, nombre) in enumerate(NIVELES):
        uzs = []
        for ci in range(6):
            tag = _tag(iz, ci)
            d = ops.nodeDisp(tag)
            uzs.append(d[2])
            if ci == 0:
                print(
                    fmt.format(tag, nombre, f"{d[0]:.6e}", f"{d[1]:.6e}", f"{d[2]:.6e}")
                )
            else:
                print(
                    fmt.format(tag, "", f"{d[0]:.6e}", f"{d[1]:.6e}", f"{d[2]:.6e}")
                )
        max_uz_nivel[nombre] = max(abs(u) for u in uzs)

    print("\n" + "=" * 72)
    print("DESPLAZAMIENTO MAXIMO POR NIVEL")
    print("=" * 72)
    for nombre, uz in max_uz_nivel.items():
        print(f"  {nombre:>8}: |Uz|_max = {uz:.6e} m ({uz*1000:.4f} mm)")

    print("\n" + "=" * 72)
    print("REACCIONES EN APOYOS (kN)")
    print("=" * 72)
    fmt_r = "{:>6} {:>14} {:>14} {:>14}"
    print(fmt_r.format("Nodo", "FX [kN]", "FY [kN]", "FZ [kN]"))
    print("-" * 72)
    RFZ = 0.0
    for ci in range(6):
        tag = _tag(0, ci)
        r = ops.nodeReaction(tag)
        RFZ += r[2]
        print(fmt_r.format(tag, f"{r[0]:.4f}", f"{r[1]:.4f}", f"{r[2]:.4f}"))
    print("-" * 72)
    print(fmt_r.format("SUMA", "0.0000", "0.0000", f"{RFZ:.4f}"))
    print(f"\nCarga vertical aplicada: {total_carga:.4f} kN")
    print(f"Reaccion vertical total: {RFZ:.4f} kN")
    print(f"Diferencia:              {abs(total_carga + RFZ):.4f} kN")

    print("\n" + "=" * 72)
    print("FUERZAS EN ELEMENTOS (eje local)")
    print("=" * 72)
    print("\n--- COLUMNAS (N_j = axial tension) ---")
    fmt_e = "{:>6} {:>6} {:>14} {:>14} {:>14}"
    print(fmt_e.format("Elem", "Nivel", "N [kN]", "Vy [kN]", "Mz [kN*m]"))
    print("-" * 62)
    for iz in range(len(NIVELES) - 1):
        for ci in range(6):
            etag = iz * 6 + ci + 1
            resp = ops.eleResponse(etag, "localForce")
            N = resp[6]
            Vy = resp[7]
            Mz = resp[11]
            nivel = f"{NIVELES[iz][1]}-{NIVELES[iz+1][1]}"
            print(fmt_e.format(etag, nivel, f"{N:.4f}", f"{Vy:.4f}", f"{Mz:.4f}"))

    print("\n--- VIGAS X (momentos de extremo My) ---")
    print(fmt_e.format("Elem", "Nivel", "My_i [kN*m]", "My_j [kN*m]", "Vz [kN]"))
    print("-" * 62)
    for idx, etag in enumerate(range(len(NIVELES) * 6 + 1, len(NIVELES) * 6 + 1 + 20)):
        resp = ops.eleResponse(etag, "localForce")
        My_i = resp[4]
        My_j = resp[10]
        Vz = resp[2]
        iz = idx // 4 + 1
        nivel = NIVELES[iz][1] if iz < len(NIVELES) else "?"
        print(fmt_e.format(etag, nivel, f"{My_i:.4f}", f"{My_j:.4f}", f"{Vz:.4f}"))


# =====================================================================
# VISUALIZACION
# =====================================================================

def visualize(ruta_salida="results/figures/edificio_3d.png"):
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(13, 9))
    ax = fig.add_subplot(projection="3d")

    nodos = {}
    desps = {}
    for iz, (z, _) in enumerate(NIVELES):
        for ci in range(6):
            tag = _tag(iz, ci)
            x, y = _col_xy(ci)
            nodos[tag] = np.array([x, y, z])
            d = ops.nodeDisp(tag)
            desps[tag] = np.array(d[:3])

    max_d = max(np.linalg.norm(d) for d in desps.values())
    escala = 5.0 / max_d if max_d > 1e-10 else 0.0

    def _linea(p1, p2, color, lw=2, ls="-", alpha=0.7):
        ax.plot(*zip(p1, p2), color=color, lw=lw, ls=ls, alpha=alpha)

    for iz in range(len(NIVELES) - 1):
        for ci in range(6):
            t1, t2 = _tag(iz, ci), _tag(iz + 1, ci)
            _linea(nodos[t1], nodos[t2], "tab:red", 2.5)
            if escala > 0:
                _linea(
                    nodos[t1] + escala * desps[t1],
                    nodos[t2] + escala * desps[t2],
                    "tab:red", 1.0, "--", 0.4,
                )

    for iz in range(1, len(NIVELES)):
        for c1, c2 in [(0, 1), (1, 2), (3, 4), (4, 5)]:
            t1, t2 = _tag(iz, c1), _tag(iz, c2)
            _linea(nodos[t1], nodos[t2], "tab:blue", 2.5)
            if escala > 0:
                _linea(
                    nodos[t1] + escala * desps[t1],
                    nodos[t2] + escala * desps[t2],
                    "tab:blue", 1.0, "--", 0.4,
                )

    for iz in range(1, len(NIVELES)):
        for ci in [0, 1, 2]:
            t1, t2 = _tag(iz, ci), _tag(iz, ci + 3)
            _linea(nodos[t1], nodos[t2], "tab:green", 2.5)
            if escala > 0:
                _linea(
                    nodos[t1] + escala * desps[t1],
                    nodos[t2] + escala * desps[t2],
                    "tab:green", 1.0, "--", 0.4,
                )

    for tag, xyz in nodos.items():
        ax.scatter(*xyz, color="k", s=12, zorder=5)

    for iz, (z, nombre) in enumerate(NIVELES):
        ax.text(17.5, 5.5, z, f"{nombre} (Z={z:.2f} m)", fontsize=7)

    for ci in range(6):
        xyz = nodos[_tag(0, ci)]
        ax.scatter(*xyz, marker="s", color="purple", s=80, depthshade=False, zorder=6)

    ax.set_xlabel("X [m]", fontsize=10)
    ax.set_ylabel("Y [m]", fontsize=10)
    ax.set_zlabel("Z [m]", fontsize=10)
    ax.set_title(
        "Edificio 3D - Proyecto 1 Grupo 4\n"
        "Col (rojo) | Viga X (azul) | Viga Y (verde) | "
        "Deformada (punteado, escala x{:.0f})".format(escala),
        fontsize=11,
    )

    manejadores = [
        plt.Line2D([0], [0], color="tab:red", lw=2.5),
        plt.Line2D([0], [0], color="tab:blue", lw=2.5),
        plt.Line2D([0], [0], color="tab:green", lw=2.5),
        plt.Line2D([0], [0], color="gray", lw=1, ls="--"),
        plt.Line2D([0], [0], marker="s", color="purple", lw=0, markersize=8),
    ]
    ax.legend(
        manejadores,
        ["Columnas", "Vigas X", "Vigas Y", "Deformada", "Apoyos"],
        loc="upper left",
        fontsize=8,
    )

    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=200)
    plt.close(fig)
    print(f"\nFigura guardada: {ruta_salida}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    print("Construyendo modelo del edificio...")
    col_tags, vx, vy = build()
    n_col = len(col_tags)
    n_vx = len(vx)
    n_vy = len(vy)
    print(f"  Nodos:    {len(NIVELES) * 6}")
    print(f"  Columnas: {n_col}")
    print(f"  Vigas X:  {n_vx}")
    print(f"  Vigas Y:  {n_vy}")
    print(f"  Total:    {n_col + n_vx + n_vy} elementos")

    print("\nAplicando peso propio de losas...")
    loads, total = apply_loads()
    print(f"  Carga vertical total: {total:.2f} kN")

    print("\nEjecutando analisis...")
    analyze()
    print("  Analisis completado exitosamente.")

    print_results(total)
    visualize()


if __name__ == "__main__":
    main()
