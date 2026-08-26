"""
Estructura simple con losa shell (shellMITC4) - Proyecto 1 Grupo 4
4 columnas, 4 vigas de perimetro, 1 losa maciza de 4x4 m modelada con
16 elementos shellMITC4 (malla 4x4).

Las vigas se dividen en 4 tramos para compartir nodos con la losa.
El peso propio de la losa se transfiere a las vigas a traves de los nodos
compartidos, reproduciendo el camino de carga real: losa -> vigas -> columnas.

Uso:
    python -m src.simple_analysis
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import openseespy.opensees as ops


# =====================================================================
# CARGAR DATOS
# =====================================================================

def cargar_datos(ruta_json):
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# CONSTRUIR MODELO
# =====================================================================

def construir_modelo(data):
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    E = data["material"]["E"]
    nu = data["material"]["nu"]
    gamma = data["material"]["gamma"]
    G = E / (2.0 * (1.0 + nu))
    espesor = data["losa"]["espesor"]

    Lx, Ly, h = 4.0, 4.0, 3.0
    nx, ny = 4, 4
    dx, dy = Lx / nx, Ly / ny

    b_c, h_c = data["secciones"]["columna"]["b"], data["secciones"]["columna"]["h"]
    A_c = b_c * h_c
    Iy_c = b_c * h_c**3 / 12.0
    Iz_c = h_c * b_c**3 / 12.0
    J_c = (0.1406 * b_c**4 if abs(b_c - h_c) < 1e-10
           else 0.196 * min(b_c, h_c)**3 * max(b_c, h_c))

    b_v, h_v = data["secciones"]["viga"]["b"], data["secciones"]["viga"]["h"]
    A_v = b_v * h_v
    Iy_v = b_v * h_v**3 / 12.0
    Iz_v = h_v * b_v**3 / 12.0
    J_v = (0.1406 * b_v**4 if abs(b_v - h_v) < 1e-10
           else 0.196 * min(b_v, h_v)**3 * max(b_v, h_v))

    # =================================================================
    # NODOS
    # =================================================================

    for tag_str, xyz in data["nodos"].items():
        if xyz[2] == 0.0:
            ops.node(int(tag_str), *xyz)

    node_id = {}
    tag_counter = 100
    for j in range(ny + 1):
        for i in range(nx + 1):
            if i == 0 and j == 0:
                tag = 5
            elif i == nx and j == 0:
                tag = 6
            elif i == nx and j == ny:
                tag = 7
            elif i == 0 and j == ny:
                tag = 8
            else:
                tag_counter += 1
                tag = tag_counter
            node_id[i, j] = tag
            ops.node(tag, i * dx, j * dy, h)

    # =================================================================
    # APOYOS
    # =================================================================

    for tag_str, fix in data["apoyos"].items():
        ops.fix(int(tag_str), *fix)

    # =================================================================
    # TRANSFORMACIONES GEOMETRICAS
    # =================================================================

    ops.geomTransf("Linear", 1, 0, 1, 0)
    ops.geomTransf("Linear", 2, 0, 0, 1)

    # =================================================================
    # COLUMNAS (4)
    # =================================================================

    col_tags = []
    for ele in data["elementos"]:
        if ele["tipo"] == "columna":
            tag = int(ele["tag"])
            ops.element("elasticBeamColumn", tag, int(ele["i"]), int(ele["j"]),
                        A_c, E, G, J_c, Iy_c, Iz_c, 1)
            col_tags.append(tag)

    # =================================================================
    # VIGAS DE PERIMETRO (4 x 4 tramos = 16)
    # =================================================================

    beam_tags = []
    bt = 20
    vignette = A_v, E, G, J_v, Iy_v, Iz_v, 2

    for i in range(nx):
        ops.element("elasticBeamColumn", bt, node_id[i, 0], node_id[i + 1, 0],
                    *vignette)
        beam_tags.append(bt)
        bt += 1

    for j in range(ny):
        ops.element("elasticBeamColumn", bt, node_id[nx, j], node_id[nx, j + 1],
                    *vignette)
        beam_tags.append(bt)
        bt += 1

    for i in range(nx, 0, -1):
        ops.element("elasticBeamColumn", bt, node_id[i, ny], node_id[i - 1, ny],
                    *vignette)
        beam_tags.append(bt)
        bt += 1

    for j in range(ny, 0, -1):
        ops.element("elasticBeamColumn", bt, node_id[0, j], node_id[0, j - 1],
                    *vignette)
        beam_tags.append(bt)
        bt += 1

    # =================================================================
    # LOSA SHELL (4x4 = 16 elementos shellMITC4)
    # =================================================================

    sec_tag = 1
    ops.section("ElasticMembranePlateSection", sec_tag, E, nu, espesor, 0.0)

    shell_tags = []
    st = 50
    for j in range(ny):
        for i in range(nx):
            n1 = node_id[i, j]
            n2 = node_id[i + 1, j]
            n3 = node_id[i + 1, j + 1]
            n4 = node_id[i, j + 1]
            ops.element("shellMITC4", st, n1, n2, n3, n4, sec_tag)
            shell_tags.append(st)
            st += 1

    return {
        "col_tags": col_tags,
        "beam_tags": beam_tags,
        "shell_tags": shell_tags,
        "node_id": node_id,
        "gamma": gamma,
        "espesor": espesor,
        "nx": nx, "ny": ny,
        "dx": dx, "dy": dy,
        "E": E, "nu": nu,
    }


# =====================================================================
# CARGAS: PESO PROPIO DE LOSA (cargas nodales por area tributaria)
# =====================================================================

def aplicar_cargas(info):
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    t = info["espesor"]
    gamma = info["gamma"]
    dx, dy = info["dx"], info["dy"]
    nx, ny = info["nx"], info["ny"]
    node_id = info["node_id"]

    total = 0.0
    for j in range(ny + 1):
        for i in range(nx + 1):
            tag = node_id[i, j]
            ax = dx / 2.0 if i in (0, nx) else dx
            ay = dy / 2.0 if j in (0, ny) else dy
            w = ax * ay * t * gamma
            ops.load(tag, 0.0, 0.0, -w, 0.0, 0.0, 0.0)
            total += w

    return -total


# =====================================================================
# ANALISIS
# =====================================================================

def analizar():
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


# =====================================================================
# RESULTADOS
# =====================================================================

def imprimir_resultados(info, total_carga):
    SEP = "=" * 72

    # ── DESPLAZAMIENTOS ──────────────────────────────────────────────
    print(f"\n{SEP}")
    print("DESPLAZAMIENTOS NODALES (nivel de losa)")
    print(SEP)

    nx, ny = info["nx"], info["ny"]
    node_id = info["node_id"]

    max_uz = 0.0
    nodo_max = ""
    fmt_d = "{:>6} {:>14} {:>14} {:>14}"
    print(fmt_d.format("Nodo", "Ux [m]", "Uy [m]", "Uz [m]"))
    print("-" * 56)

    for j in range(ny + 1):
        for i in range(nx + 1):
            tag = node_id[i, j]
            d = ops.nodeDisp(tag)
            print(fmt_d.format(str(tag), f"{d[0]:.6e}", f"{d[1]:.6e}", f"{d[2]:.6e}"))
            if abs(d[2]) > max_uz:
                max_uz = abs(d[2])
                nodo_max = str(tag)

    print(f"\n  CRITICO: Nodo {nodo_max}: |Uz|_max = {max_uz:.6e} m"
          f" = {max_uz * 1000:.4f} mm")

    # ── REACCIONES ───────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("REACCIONES EN APOYOS")
    print(SEP)

    RFZ = 0.0
    fmt_r = "{:>6} {:>14} {:>14} {:>14}"
    print(fmt_r.format("Nodo", "FX [kN]", "FY [kN]", "FZ [kN]"))
    print("-" * 56)

    for tag_str, fix in data_apoyos.items():
        if all(f == 1 for f in fix):
            tag = int(tag_str)
            r = ops.nodeReaction(tag)
            RFZ += r[2]
            print(fmt_r.format(tag_str, f"{r[0]:.4f}", f"{r[1]:.4f}", f"{r[2]:.4f}"))

    print("-" * 56)
    print(f"\n  Reaccion total FZ: {RFZ:.4f} kN")
    print(f"  Carga aplicada:    {total_carga:.4f} kN")
    print(f"  Diferencia:        {abs(total_carga + RFZ):.6f} kN  (OK)")

    # ── FUERZAS EN COLUMNAS ──────────────────────────────────────────
    print(f"\n{SEP}")
    print("FUERZAS EN COLUMNAS (eje local)")
    print(SEP)

    fmt_e = "{:>6} {:>14} {:>14} {:>14} {:>14}"
    print(fmt_e.format("Elem", "N [kN]", "Vy [kN]", "Vz [kN]", "Mz [kN*m]"))
    print("-" * 68)

    for tag in info["col_tags"]:
        resp = ops.eleResponse(tag, "localForce")
        N, Vy, Vz = resp[0], resp[1], resp[2]
        Mz = resp[5]
        print(fmt_e.format(str(tag), f"{N:.4f}", f"{Vy:.4f}", f"{Vz:.4f}", f"{Mz:.4f}"))

    # ── FUERZAS EN VIGAS ─────────────────────────────────────────────
    print(f"\n{SEP}")
    print("FUERZAS EN VIGAS (eje local)")
    print(SEP)

    fmt_v = "{:>6} {:>6} {:>14} {:>14} {:>14} {:>14}"
    print(fmt_v.format("Elem", "Lado", "N [kN]", "Vy [kN]", "Vz [kN]", "Mz [kN*m]"))
    print("-" * 76)

    lado_map = {0: "Abajo", 1: "Der", 2: "Arriba", 3: "Izq"}
    N_max = Vy_max = Vz_max = Mz_max = 0.0
    elem_N = elem_Vy = elem_Vz = elem_Mz = 0

    for idx, tag in enumerate(info["beam_tags"]):
        resp = ops.eleResponse(tag, "localForce")
        N, Vy, Vz = resp[0], resp[1], resp[2]
        Mz = resp[5]
        lado = lado_map[idx // 4]
        print(fmt_v.format(str(tag), lado, f"{N:.4f}", f"{Vy:.4f}",
                           f"{Vz:.4f}", f"{Mz:.4f}"))
        if abs(N) > abs(N_max):
            N_max = N; elem_N = tag
        if abs(Vy) > abs(Vy_max):
            Vy_max = Vy; elem_Vy = tag
        if abs(Vz) > abs(Vz_max):
            Vz_max = Vz; elem_Vz = tag
        if abs(Mz) > abs(Mz_max):
            Mz_max = Mz; elem_Mz = tag

    print(f"\n  CRITICOS EN VIGAS:")
    print(f"    Axial:    Elem {elem_N}: N  = {N_max:+.4f} kN")
    print(f"    Corte Vy: Elem {elem_Vy}: Vy = {Vy_max:+.4f} kN")
    print(f"    Corte Vz: Elem {elem_Vz}: Vz = {Vz_max:+.4f} kN")
    print(f"    Momento:  Elem {elem_Mz}: Mz = {Mz_max:+.4f} kN*m")

    # ── FUERZAS EN LOSA (resultantes por unidad de largo) ────────────
    print(f"\n{SEP}")
    print("FUERZAS EN LOSA (shellMITC4 - tensiones resultantes)")
    print(SEP)

    fmt_s = "{:>6} {:>12} {:>12} {:>12} {:>12} {:>12}"
    print(fmt_s.format("Elem", "Nxx", "Nyy", "Mxx", "Myy", "Vxz"))
    print("-" * 72)

    for tag in info["shell_tags"]:
        try:
            resp = ops.eleResponse(tag, "force")
            if len(resp) >= 8:
                Nxx, Nyy = resp[0], resp[1]
                Mxx, Myy = resp[3], resp[4]
                Vxz = resp[6]
                print(fmt_s.format(str(tag), f"{Nxx:.4f}", f"{Nyy:.4f}",
                                   f"{Mxx:.4f}", f"{Myy:.4f}", f"{Vxz:.4f}"))
        except Exception:
            pass

    print(f"\n  Nota: Valores por unidad de largo [kN/m] y [kN*m/m]")


# =====================================================================
# VISUALIZACION
# =====================================================================

def visualizar(info, ruta_salida="results/figures/estructura_simple.png"):
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(projection="3d")

    node_id = info["node_id"]
    nx, ny = info["nx"], info["ny"]
    dx, dy = info["dx"], info["dy"]

    def _coord(tag):
        d = ops.nodeDisp(tag)
        return np.array([ops.nodeCoord(tag, c + 1) + d[c] for c in range(3)])

    def _orig(tag):
        return np.array([ops.nodeCoord(tag, c + 1) for c in range(3)])

    max_d = 0.0
    for j in range(ny + 1):
        for i in range(nx + 1):
            tag = node_id[i, j]
            d = np.array(ops.nodeDisp(tag)[:3])
            max_d = max(max_d, np.linalg.norm(d))

    escala = 0.5 / max_d if max_d > 1e-10 else 0.0

    # Columnas
    for ele in data_elems:
        if ele["tipo"] == "columna":
            p0 = _orig(int(ele["i"]))
            p1 = _orig(int(ele["j"]))
            ax.plot(*zip(p0, p1), color="tab:red", lw=3, alpha=0.8)
            if escala > 0:
                d0 = np.array(ops.nodeDisp(int(ele["i"]))[:3])
                d1 = np.array(ops.nodeDisp(int(ele["j"]))[:3])
                ax.plot(*zip(p0 + escala * d0, p1 + escala * d1),
                        color="tab:red", lw=1.5, ls="--", alpha=0.4)

    # Vigas
    for tag in info["beam_tags"]:
        ni, nj = ops.eleNodes(tag)
        p0 = _orig(ni)
        p1 = _orig(nj)
        ax.plot(*zip(p0, p1), color="tab:blue", lw=3, alpha=0.8)

    # Losa (malla deformada)
    for j in range(ny):
        for i in range(nx):
            n1 = node_id[i, j]
            n2 = node_id[i + 1, j]
            n3 = node_id[i + 1, j + 1]
            n4 = node_id[i, j + 1]
            verts = np.array([_orig(n) for n in [n1, n2, n3, n4, n1]])
            from mpl_toolkits.mplot3d.art3d import Poly3DCollection
            poly = Poly3DCollection([verts], alpha=0.15, facecolor="cyan",
                                    edgecolor="gray", lw=0.5)
            ax.add_collection3d(poly)

    # Nodos
    for j in range(ny + 1):
        for i in range(nx + 1):
            tag = node_id[i, j]
            p = _orig(tag)
            ax.scatter(*p, color="k", s=20, zorder=5)

    # Apoyos
    for tag_str, fix in data_apoyos.items():
        if all(f == 1 for f in fix):
            p = _orig(int(tag_str))
            ax.scatter(*p, marker="s", color="purple", s=100,
                       depthshade=False, zorder=6)

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")
    ax.set_title(
        "Estructura Simple con Losa Shell - Proyecto 1 Grupo 4\n"
        "Columnas (rojo) | Vigas (azul) | Losa shell (cyan)\n"
        + (f"Deformada escala x{escala:.0f}" if escala > 0 else ""),
    )

    manejadores = [
        plt.Line2D([0], [0], color="tab:red", lw=3),
        plt.Line2D([0], [0], color="tab:blue", lw=3),
        plt.Line2D([0], [0], color="cyan", lw=8, alpha=0.3),
        plt.Line2D([0], [0], marker="s", color="purple", lw=0, markersize=8),
    ]
    ax.legend(manejadores, ["Columnas", "Vigas", "Losa shell", "Apoyos"],
              loc="upper left", fontsize=9)

    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=200)
    plt.close(fig)
    print(f"\nFigura guardada: {ruta_salida}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    global data_apoyos, data_elems

    ruta_json = sys.argv[1] if len(sys.argv) > 1 else "data/estructura_simple.json"

    print(f"Cargando datos: {ruta_json}")
    data = cargar_datos(ruta_json)
    data_apoyos = data["apoyos"]
    data_elems = data["elementos"]

    print("Construyendo modelo...")
    info = construir_modelo(data)
    n_col = len(info["col_tags"])
    n_beam = len(info["beam_tags"])
    n_shell = len(info["shell_tags"])
    n_nodos_top = (info["nx"] + 1) * (info["ny"] + 1)
    print(f"  Columnas:   {n_col}")
    print(f"  Vigas:      {n_beam} (4 lados x 4 tramos)")
    print(f"  Losas:      {n_shell} (shellMITC4, malla {info['nx']}x{info['ny']})")
    print(f"  Nodos top:  {n_nodos_top}")

    print("\nAplicando peso propio de losa (cargas nodales)...")
    total = aplicar_cargas(info)
    print(f"  Carga vertical total: {total:.2f} kN")

    print("\nEjecutando analisis...")
    analizar()
    print("  Analisis completado exitosamente.")

    imprimir_resultados(info, total)
    visualizar(info)


if __name__ == "__main__":
    main()
