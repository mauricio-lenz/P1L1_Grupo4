"""Visualizacion simple del modelo: geometria, apoyos, cargas y ejes locales.

Los ejes locales se calculan con la misma convencion de geomTransf Linear
de OpenSees: x = (pJ - pI) normalizado; z = vecxz proyectado perpendicular
a x; y = z cruz x.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _ejes_locales(p_i, p_j, vecxz):
    x = np.subtract(p_j, p_i, dtype=float)
    x = x / np.linalg.norm(x)
    vz = np.asarray(vecxz, dtype=float)
    if abs(np.dot(vz, x)) > 1.0 - 1.0e-9:
        raise ValueError("vecxz paralelo al eje del elemento")
    z = vz - np.dot(vz, x) * x
    z = z / np.linalg.norm(z)
    y = np.cross(z, x)
    return x, y, z


def graficar_caso(data, desplazamientos=None, ruta_salida="figura.png", escala_deformada=50.0):
    nodos = {int(t): np.asarray(xyz, float) for t, xyz in data["nodos"].items()}
    transf = {nombre: t["vecxz"] for nombre, t in data["transformaciones"].items()}

    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(projection="3d")

    for ele in data["elementos"]:
        p_i, p_j = nodos[ele["i"]], nodos[ele["j"]]
        color = "tab:blue" if ele["tipo"] == "viga" else "tab:red"
        ax.plot(*zip(p_i, p_j), color=color, lw=3, label=f"_{ele['tipo']}")
        mid = (p_i + p_j) / 2.0
        xl, yl, zl = _ejes_locales(p_i, p_j, transf[ele["transf"]])
        LARGO = 0.45
        for eje, color_eje in ((xl, "r"), (yl, "g"), (zl, "b")):
            ax.quiver(
                mid[0], mid[1], mid[2],
                eje[0], eje[1], eje[2],
                color=color_eje, lw=1.5, arrow_length_ratio=0.15,
            )
        etiqueta = f"{ele['tag']}: {ele['i']}-{ele['j']}"
        ax.text(mid[0], mid[1], mid[2] + 0.15, etiqueta, fontsize=7)

    for tag, xyz in nodos.items():
        ax.scatter(*xyz, color="k", s=25)
        ax.text(xyz[0], xyz[1], xyz[2] + 0.12, str(tag), fontsize=9, weight="bold")

    for tag_str in data["apoyos"]:
        xyz = nodos[int(tag_str)]
        ax.scatter(*xyz, marker="s", color="purple", s=90, depthshade=False)

    for carga in data["cargas_nodales"]:
        xyz = nodos[int(carga["nodo"])]
        f = np.asarray(carga["fxyz"], dtype=float)
        magnitud = np.linalg.norm(f)
        if magnitud > 0:
            ax.quiver(
                xyz[0], xyz[1], xyz[2],
                *(f / magnitud),
                color="darkorange", lw=2.5, arrow_length_ratio=0.15,
            )

    if desplazamientos is not None:
        for ele in data["elementos"]:
            p_i = nodos[ele["i"]] + escala_deformada * np.asarray(
                desplazamientos[str(ele["i"])][:3]
            )
            p_j = nodos[ele["j"]] + escala_deformada * np.asarray(
                desplazamientos[str(ele["j"])][:3]
            )
            ax.plot(*zip(p_i, p_j), color="gray", ls="--", lw=1.2)

    ax.set_xlabel("X [m]")
    ax.set_ylabel("Y [m]")
    ax.set_zlabel("Z [m]")
    ax.set_title(
        f"{data['nombre']} - geometria, ejes locales (x rojo, y verde, z azul), "
        "apoyos (cuadrado morado), cargas (naranjo)"
    )

    manejadores = [
        plt.Line2D([0], [0], color="tab:blue", lw=3),
        plt.Line2D([0], [0], color="tab:red", lw=3),
        plt.Line2D([0], [0], color="gray", ls="--", lw=1.2),
    ]
    ax.legend(manejadores, ["vigas", "columnas", "deformada (escala aumentada)"])

    fig.tight_layout()
    fig.savefig(ruta_salida, dpi=200)
    plt.close(fig)
