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
    python -m src.portico_3d data/portico_3d.json
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


def prop_seccion(b, h, E):
    G = E / (2.0 * (1.0 + 0.20))
    A = b * h
    Iy = b * h**3 / 12.0
    Iz = h * b**3 / 12.0
    if abs(b - h) < 1e-10:
        J = 0.1406 * b**4
    else:
        J = 0.196 * min(b, h)**3 * max(b, h)
    return A, E, G, J, Iy, Iz


# =====================================================================
# CONSTRUIR MODELO
# =====================================================================

def construir_modelo(data):
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    E = data["material"]["E"]
    nu = data["material"]["nu"]
    G = E / (2.0 * (1.0 + nu))
    ops.uniaxialMaterial("Elastic", 1, E)

    # --- Secciones ---
    sec = {}
    for nombre, s in data["secciones"].items():
        sec[nombre] = prop_seccion(s["b"], s["h"], E)

    # --- Nodos ---
    for tag_str, xyz in data["nodos"].items():
        ops.node(int(tag_str), *xyz)

    # --- Apoyos ---
    for tag_str, fix in data["apoyos"].items():
        ops.fix(int(tag_str), *fix)

    # --- Transformaciones geometricas ---
    for nombre, gt in data["geomTransf"].items():
        ops.geomTransf("Linear", int(gt["tag"]), *gt["vecxz"])

    # --- Elementos ---
    for ele in data["elementos"]:
        tag = int(ele["tag"])
        ni = int(ele["i"])
        nj = int(ele["j"])
        params = sec[ele["seccion"]]
        transf_tag = int(data["geomTransf"][ele["transf"]]["tag"])
        ops.element("elasticBeamColumn", tag, ni, nj, *params, transf_tag)

    return sec


# =====================================================================
# CARGAS DISTRIBUIDAS (peso de losa sobre vigas)
# =====================================================================

def aplicar_cargas(data):
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)

    total = 0.0
    for ele in data["elementos"]:
        wy = ele.get("carga_wy", 0.0)
        wz = ele.get("carga_wz", 0.0)
        if wy != 0.0 or wz != 0.0:
            ops.eleLoad("-ele", int(ele["tag"]), "-type", "-beamUniform", wy, wz)
            ni = int(ele["i"])
            nj = int(ele["j"])
            xi = np.array(data["nodos"][str(ni)])
            xj = np.array(data["nodos"][str(nj)])
            L = np.linalg.norm(xj - xi)
            total += (wy + wz) * L

    return total


# =====================================================================
# ANALISIS
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

def imprimir_resultados(data, carga_aplicada):
    SEP = "=" * 78

    nodos_apoyo = [int(t) for t, fix in data["apoyos"].items()
                   if all(f == 1 for f in fix)]
    nodos_top = sorted(int(t) for t, xyz in data["nodos"].items() if xyz[2] > 0)
    col_tags = [int(e["tag"]) for e in data["elementos"] if e["tipo"] == "columna"]

    # ── REACCIONES BASE ─────────────────────────────────────────────
    print(f"\n{SEP}")
    print("REACCIONES EN LA BASE (apoyos empotrados)")
    print(SEP)
    print(f"{'Nodo':>6} {'FX [kN]':>12} {'FY [kN]':>12} {'FZ [kN]':>12}"
          f" {'MX [kN*m]':>12} {'MY [kN*m]':>12} {'MZ [kN*m]':>12}")
    print("-" * 78)

    sum_fx = sum_fy = sum_fz = 0.0
    for tag in nodos_apoyo:
        r = ops.nodeReaction(tag)
        sum_fx += r[0]
        sum_fy += r[1]
        sum_fz += r[2]
        print(f"{tag:>6} {r[0]:>12.4f} {r[1]:>12.4f} {r[2]:>12.4f}"
              f" {r[3]:>12.4f} {r[4]:>12.4f} {r[5]:>12.4f}")

    print("-" * 78)
    print(f"  Suma FX = {sum_fx:.4f} kN    Suma FY = {sum_fy:.4f} kN    Suma FZ = {sum_fz:.4f} kN")

    # ── VERIFICACION ────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("VERIFICACION DE EQUILIBRIO")
    print(SEP)
    print(f"  Carga total aplicada (peso losa):    {carga_aplicada:>10.4f} kN")
    print(f"  Suma de reacciones FZ (apoyos):      {sum_fz:>10.4f} kN")
    dif = abs(carga_aplicada) - abs(sum_fz)
    print(f"  Diferencia:                          {dif:>10.6f} kN")
    if abs(dif) < 1e-6:
        print(f"  Estado: CUMPLE  (|diff| < 1e-6 kN)")
    else:
        print(f"  Estado: NO CUMPLE (|diff| = {abs(dif):.6f} kN)")
    print(SEP)

    # ── DESPLAZAMIENTOS NODALES ─────────────────────────────────────
    print(f"\n{SEP}")
    print("DESPLAZAMIENTOS - NIVEL TECHO")
    print(SEP)
    print(f"{'Nodo':>6} {'Ux [m]':>14} {'Uy [m]':>14} {'Uz [m]':>14}"
          f" {'Rx [rad]':>14} {'Ry [rad]':>14} {'Rz [rad]':>14}")
    print("-" * 86)

    for tag in nodos_top:
        d = ops.nodeDisp(tag)
        print(f"{tag:>6} {d[0]:>14.6e} {d[1]:>14.6e} {d[2]:>14.6e}"
              f" {d[3]:>14.6e} {d[4]:>14.6e} {d[5]:>14.6e}")

    # ── VERIFICACION: DESPLAZAMIENTO DE UN NODO ─────────────────────
    print(f"\n{SEP}")
    print("VERIFICACION: DESPLAZAMIENTO DE UN NODO")
    print(SEP)
    for tag in nodos_top:
        d = ops.nodeDisp(tag)
        print(f"  Nodo {tag}:  Ux={d[0]:>12.6e} m   Uy={d[1]:>12.6e} m   "
              f"Uz={d[2]:>12.6e} m")
    print(SEP)

    # ── FUERZAS INTERNAS DE TODOS LOS ELEMENTOS ─────────────────────
    print(f"\n{SEP}")
    print("FUERZAS INTERNAS - ELEMENTOS (eje local)")
    print(SEP)

    for ele in data["elementos"]:
        tag = int(ele["tag"])
        ni, nj = int(ele["i"]), int(ele["j"])
        resp = ops.eleResponse(tag, "localForce")
        print(f"\n  Elemento {tag}: {ele['tipo']}  (Nodos {ni} -> {nj})")
        print(f"    Nodo i:  N={resp[0]:>10.4f}  Vy={resp[1]:>10.4f}"
              f"  Vz={resp[2]:>10.4f}  T={resp[3]:>10.4f}"
              f"  My={resp[4]:>10.4f}  Mz={resp[5]:>10.4f}")
        print(f"    Nodo j:  N={resp[6]:>10.4f}  Vy={resp[7]:>10.4f}"
              f"  Vz={resp[8]:>10.4f}  T={resp[9]:>10.4f}"
              f"  My={resp[10]:>10.4f}  Mz={resp[11]:>10.4f}")

    # ── VERIFICACION: FUERZA AXIAL DE UN ELEMENTO ───────────────────
    print(f"\n{SEP}")
    print("VERIFICACION: FUERZA AXIAL EN COLUMNAS")
    print(SEP)
    n_col = len(col_tags) if col_tags else 0
    n_apoyo = len(nodos_apoyo)
    for tag in col_tags:
        r = ops.eleResponse(tag, "localForce")
        N = r[0]
        print(f"  Elemento {tag}:  Fuerza axial N = {N:>10.4f} kN")
    if n_col > 0 and n_apoyo > 0:
        N_esp = carga_aplicada / n_apoyo
        print(f"\n  Esperado (peso total / {n_apoyo} apoyos): {N_esp:>8.4f} kN")
    print(SEP)

    # ── VERIFICACION: MOMENTO DE EXTREMO DE UN ELEMENTO ─────────────
    print(f"\n{SEP}")
    print("VERIFICACION: MOMENTO EN EXTREMO DE COLUMNAS")
    print(SEP)
    for tag in col_tags:
        r = ops.eleResponse(tag, "localForce")
        My_i, Mz_i = r[4], r[5]
        My_j, Mz_j = r[10], r[11]
        print(f"  Elemento {tag}:")
        print(f"    Nodo i:  My={My_i:>10.4f} kN*m   Mz={Mz_i:>10.4f} kN*m")
        print(f"    Nodo j:  My={My_j:>10.4f} kN*m   Mz={Mz_j:>10.4f} kN*m")
    print(SEP)

    _resumen_criticos(data)


def _resumen_criticos(data):
    SEP = "=" * 78

    col_tags = [int(e["tag"]) for e in data["elementos"] if e["tipo"] == "columna"]
    vig_corta_tags = [int(e["tag"]) for e in data["elementos"] if e["tipo"] == "viga_corta"]
    vig_larga_tags = [int(e["tag"]) for e in data["elementos"] if e["tipo"] == "viga_larga"]

    N_col_max = 0.0
    M_col_max = 0.0
    for tag in col_tags:
        r = ops.eleResponse(tag, "localForce")
        N = min(r[0], r[6])
        M = max(abs(r[4]), abs(r[5]), abs(r[10]), abs(r[11]))
        if abs(N) > abs(N_col_max):
            N_col_max = N
        if M > M_col_max:
            M_col_max = M

    M_vc_max = V_vc_max = 0.0
    for tag in vig_corta_tags:
        r = ops.eleResponse(tag, "localForce")
        M = max(abs(r[4]), abs(r[5]), abs(r[10]), abs(r[11]))
        V = max(abs(r[1]), abs(r[2]), abs(r[7]), abs(r[8]))
        if M > M_vc_max: M_vc_max = M
        if V > V_vc_max: V_vc_max = V

    M_vl_max = V_vl_max = 0.0
    for tag in vig_larga_tags:
        r = ops.eleResponse(tag, "localForce")
        M = max(abs(r[4]), abs(r[5]), abs(r[10]), abs(r[11]))
        V = max(abs(r[1]), abs(r[2]), abs(r[7]), abs(r[8]))
        if M > M_vl_max: M_vl_max = M
        if V > V_vl_max: V_vl_max = V

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

def visualizar(data, ruta_salida="results/figures/portico_3d.png"):
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(projection="3d")

    def _coord(tag):
        return np.array(data["nodos"][str(tag)], float)

    def _disp(tag):
        return np.array(ops.nodeDisp(tag)[:3])

    all_tags = [int(t) for t in data["nodos"]]
    max_d = max(np.linalg.norm(_disp(t)) for t in all_tags)
    escala = 0.3 / max_d if max_d > 1e-10 else 0.0

    for ele in data["elementos"]:
        ni, nj = int(ele["i"]), int(ele["j"])
        p0 = _coord(ni)
        p1 = _coord(nj)
        es_col = ele["tipo"] == "columna"
        color = "tab:red" if es_col else "tab:blue"

        ax.plot(*zip(p0, p1), color=color, lw=3, alpha=0.7)

        if escala > 0:
            d0 = _disp(ni)
            d1 = _disp(nj)
            ax.plot(*zip(p0 + escala * d0, p1 + escala * d1),
                    color=color, lw=2, ls="--", alpha=0.5)

    for tag in all_tags:
        p = _coord(tag)
        ax.scatter(*p, color="k", s=30, zorder=5)
        ax.text(p[0], p[1], p[2] + 0.15, str(tag),
                fontsize=11, weight="bold", ha="center")

    for tag_str, fix in data["apoyos"].items():
        if all(f == 1 for f in fix):
            p = _coord(int(tag_str))
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
    ruta_json = sys.argv[1] if len(sys.argv) > 1 else "data/portico_3d.json"

    print("=" * 78)
    print("PORTICO 3D - ANALISIS ESTATICO LINEAL")
    print("Proyecto 1 Grupo 4")
    print("=" * 78)

    print(f"\nCargando datos: {ruta_json}")
    data = cargar_datos(ruta_json)

    n_col = sum(1 for e in data["elementos"] if e["tipo"] == "columna")
    n_vig = sum(1 for e in data["elementos"] if "viga" in e["tipo"])

    print(f"\n[1] Construyendo modelo...")
    sec = construir_modelo(data)
    print(f"    {len(data['nodos'])} nodos, {len(data['elementos'])} elementos ({n_col} col + {n_vig} vig)")

    print(f"\n[2] Aplicando cargas distribuidas (peso de losa)...")
    total = aplicar_cargas(data)
    print(f"    Carga total aplicada: {total:.4f} kN")

    print(f"\n[3] Ejecutando analisis...")
    analizar()
    print("    Analisis completado.")

    print(f"\n[4] Extrayendo resultados...")
    imprimir_resultados(data, total)

    print("[5] Generando visualizacion 3D...")
    visualizar(data)


if __name__ == "__main__":
    main()
