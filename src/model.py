"""Construccion del modelo OpenSees a partir de los datos JSON del caso.

Contrato de datos (unidades SI: m, kN, kN/m2, kN*m):
- secciones: propiedades rectangulares b x h; A, Iy e Iz se calculan aqui.
- transformaciones: nombre -> vecxz.
- nodos: tag -> [x, y, z] (m).
- apoyos: tag -> 6 valores 0/1 (uX, uY, uZ, rX, rY, rZ).
- elementos: {tag, i, j, seccion, transf, tipo}.
- cargas_nodales: {nodo, fxyz, mxyz} (kN y kN*m).
"""

import json

import openseespy.opensees as ops


def cargar_caso(ruta_json):
    with open(ruta_json, "r", encoding="utf-8") as f:
        return json.load(f)


def propiedades_seccion(sec):
    """Calcula A, Iy, Iz a partir de b, h y valida que sean positivos."""
    b = float(sec["b"])
    h = float(sec["h"])
    A = b * h
    Iy = b * h**3 / 12.0
    Iz = h * b**3 / 12.0
    if A <= 0.0 or Iy <= 0.0 or Iz <= 0.0:
        raise ValueError(f"Seccion con propiedad no positiva: b={b}, h={h}")
    return {"A": A, "Iy": Iy, "Iz": Iz}


def construir_modelo(data):
    """Levanta en OpenSees el modelo definido por data (tras ops.wipe())."""
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)

    secciones = {}
    for nombre, sec in data["secciones"].items():
        props = propiedades_seccion(sec)
        G = sec["E"] / (2.0 * (1.0 + sec["nu"]))
        secciones[nombre] = {
            "A": props["A"],
            "Iy": props["Iy"],
            "Iz": props["Iz"],
            "J": float(sec["J"]),
            "E": float(sec["E"]),
            "G": G,
        }
        if secciones[nombre]["J"] <= 0.0:
            raise ValueError(f"Seccion {nombre} con J no positivo")

    for tag_str, xyz in data["nodos"].items():
        ops.node(int(tag_str), *xyz)

    for tag_str, restricciones in data["apoyos"].items():
        ops.fix(int(tag_str), *restricciones)

    tags_transf = {
        nombre: tag
        for tag, nombre in enumerate(data["transformaciones"], start=1)
    }
    for nombre, tag in tags_transf.items():
        vecxz = data["transformaciones"][nombre]["vecxz"]
        ops.geomTransf("Linear", tag, *vecxz)

    for ele in data["elementos"]:
        sec = secciones[ele["seccion"]]
        transf_tag = tags_transf[ele["transf"]]
        i_tag = int(ele["i"])
        j_tag = int(ele["j"])
        if i_tag not in ops.getNodeTags() or j_tag not in ops.getNodeTags():
            raise ValueError(
                f"Elemento {ele['tag']} conecta nodos inexistentes: {i_tag}, {j_tag}"
            )
        ops.element(
            "elasticBeamColumn",
            int(ele["tag"]),
            i_tag,
            j_tag,
            sec["A"],
            sec["E"],
            sec["G"],
            sec["J"],
            sec["Iy"],
            sec["Iz"],
            transf_tag,
        )

    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for carga in data["cargas_nodales"]:
        ops.load(int(carga["nodo"]), *carga["fxyz"], *carga["mxyz"])
