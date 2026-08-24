"""Soluciones analiticas independientes para verificar los modelos.

Estas soluciones NO usan OpenSees. Cualquier discrepancia grande indica un
error de modelo (unidades, ejes, apoyos o secciones), no de la formula.

El marco se resuelve como PORTICO PLANO en el plano X-Z (la respuesta 3D
tiene uy = rX = rZ = 0 por simetria, lo que se verifica aparte):
- 3 grados de libertad por nodo: ux, uz, theta_y.
- Elemento de rigidez directa: barra + flexion Euler-Bernoulli con
  deformacion axial (necesaria: el vuelco estira/acomoda las columnas e
  inclina la cuerda de la viga; ignorarlo da errores de ~15%).
"""

import math

import numpy as np


def _distancia(p, q):
    return math.sqrt(sum((pi - qi) ** 2 for pi, qi in zip(p, q)))


def _propiedades(data, nombre_seccion):
    sec = data["secciones"][nombre_seccion]
    b, h = float(sec["b"]), float(sec["h"])
    return {
        "A": b * h,
        "Iy": b * h**3 / 12.0,
        "Iz": h * b**3 / 12.0,
        "E": float(sec["E"]),
    }


def _elementos_por_tipo(data):
    por_tipo = {}
    for ele in data["elementos"]:
        por_tipo.setdefault(ele["tipo"], []).append(ele)
    return por_tipo


def solucion_voladizo(data):
    """Voladizo Euler-Bernoulli con carga puntual P en la punta.

    delta = P L^3 / (3 E Iy); Rz = P en el apoyo;
    momento en el empotramiento (magnitud) = P L; axial nula.
    """
    tags_nodos = list(data["nodos"])
    p_i = data["nodos"][tags_nodos[0]]
    p_j = data["nodos"][tags_nodos[1]]
    L = _distancia(p_i, p_j)

    carga = data["cargas_nodales"][0]
    P = abs(carga["fxyz"][2])

    sec = _propiedades(data, data["elementos"][0]["seccion"])
    delta = P * L**3 / (3.0 * sec["E"] * sec["Iy"])

    return {
        "P": P,
        "L": L,
        "delta_punta": delta,
        "Rz_apoyo": P,
        "M_empotramiento": P * L,
        "N_viga": 0.0,
    }


def _rigidez_portico(E, A, I, L, c, s):
    """Matriz 6x6 del portico plano en ejes globales.

    DOF locales: [u_i, w_i, th_i, u_j, w_j, th_j].
    c, s: coseno/seno del angulo del eje local x respecto a X global.
    Flexion Euler-Bernoulli (sin deformacion de corte) + axial.
    """
    k_loc = np.zeros((6, 6))
    ea_l = E * A / L
    ei_l3 = E * I / L**3
    k_loc[0, 0] = ea_l
    k_loc[0, 3] = -ea_l
    k_loc[3, 0] = -ea_l
    k_loc[3, 3] = ea_l
    flexion = np.array(
        [
            [12.0, 6.0 * L, -12.0, 6.0 * L],
            [6.0 * L, 4.0 * L * L, -6.0 * L, 2.0 * L * L],
            [-12.0, -6.0 * L, 12.0, -6.0 * L],
            [6.0 * L, 2.0 * L * L, -6.0 * L, 4.0 * L * L],
        ],
        dtype=float,
    )
    # DOF locales: u=[0,3], w=[1,4], theta=[2,5]. El bloque de flexion
    # acopla (w_i, th_i) con (w_j, th_j).
    wi, ti, wj, tj = 1, 2, 4, 5
    k_loc[np.ix_([wi, ti], [wi, ti])] += ei_l3 * flexion[0:2, 0:2]
    k_loc[np.ix_([wi, ti], [wj, tj])] += ei_l3 * flexion[0:2, 2:4]
    k_loc[np.ix_([wj, tj], [wi, ti])] += ei_l3 * flexion[2:4, 0:2]
    k_loc[np.ix_([wj, tj], [wj, tj])] += ei_l3 * flexion[2:4, 2:4]

    # Rotacion local -> global en el plano (ux, uz, ry por nodo).
    T = np.zeros((6, 6))
    for nodo in range(2):
        i0 = 3 * nodo
        T[i0, i0] = c
        T[i0, i0 + 1] = s
        T[i0 + 1, i0] = -s
        T[i0 + 1, i0 + 1] = c
        T[i0 + 2, i0 + 2] = 1.0
    return T.T @ k_loc @ T


def solucion_marco(data):
    """Portico plano por rigidez directa (verificacion independiente)."""
    tags = sorted(int(t) for t in data["nodos"])
    indice = {tag: i for i, tag in enumerate(tags)}
    ndof = 3 * len(tags)

    cargas = {tag: np.zeros(3) for tag in tags}
    for carga in data["cargas_nodales"]:
        # Portico plano X-Z: DOF [ux, uz, ry] <- globales [FX, FZ, MY].
        cargas[int(carga["nodo"])] += np.array(
            [carga["fxyz"][0], carga["fxyz"][2], carga["mxyz"][1]]
        )

    K = np.zeros((ndof, ndof))
    F = np.zeros(ndof)
    for tag in tags:
        i0 = 3 * indice[tag]
        F[i0 : i0 + 3] += cargas[tag]

    elementos_info = []
    for ele in data["elementos"]:
        ni, nj = int(ele["i"]), int(ele["j"])
        pi = np.asarray(data["nodos"][str(ni)], float)
        pj = np.asarray(data["nodos"][str(nj)], float)
        L = float(np.linalg.norm(pj - pi))
        d = (pj - pi) / L
        c, s = d[0], d[2]
        sec = _propiedades(data, ele["seccion"])
        k = _rigidez_portico(sec["E"], sec["A"], sec["Iy"], L, c, s)
        mapa = [
            3 * indice[ni],
            3 * indice[ni] + 1,
            3 * indice[ni] + 2,
            3 * indice[nj],
            3 * indice[nj] + 1,
            3 * indice[nj] + 2,
        ]
        for a in range(6):
            for b in range(6):
                K[mapa[a], mapa[b]] += k[a, b]
        elementos_info.append({"ele": ele, "mapa": mapa, "L": L, "c": c, "s": s})

    libres = []
    for tag in tags:
        i0 = 3 * indice[tag]
        if str(tag) in data["apoyos"]:
            continue
        libres.extend([i0, i0 + 1, i0 + 2])
    u = np.zeros(ndof)
    u[libres] = np.linalg.solve(K[np.ix_(libres, libres)], F[libres])

    def desplazamiento(tag):
        i0 = 3 * indice[tag]
        return u[i0 : i0 + 3]

    salida = {"deriva": float(desplazamiento(nodos_superiores(data)[0])[0])}

    axiales = {}
    momentos_base = {}
    momentos_top = {}
    for info in elementos_info:
        ele = info["ele"]
        u_e = np.concatenate([desplazamiento(int(ele["i"])), desplazamiento(int(ele["j"]))])
        ni, nj = int(ele["i"]), int(ele["j"])
        pi = np.asarray(data["nodos"][str(ni)], float)
        pj = np.asarray(data["nodos"][str(nj)], float)
        L = info["L"]
        c, s = info["c"], info["s"]
        sec = _propiedades(data, ele["seccion"])
        # Alargamiento axial (positivo = tension): proyeccion de la
        # diferencia de desplazamientos sobre el eje del elemento.
        du_xz = np.array([u_e[3] - u_e[0], u_e[4] - u_e[1]])
        N = sec["E"] * sec["A"] * (c * du_xz[0] + s * du_xz[1]) / L
        # Momentos de extremo (portico plano):
        # giro de cuerda psi = w_rel/L con w_loc = -s*ux + c*uz.
        w_rel = -s * du_xz[0] + c * du_xz[1]
        psi = w_rel / L
        th_i, th_j = u_e[2], u_e[5]
        ei_l = sec["E"] * sec["Iy"] / L
        M_i = ei_l * (4.0 * th_i + 2.0 * th_j - 6.0 * psi)
        M_j = ei_l * (2.0 * th_i + 4.0 * th_j - 6.0 * psi)
        axiales[str(ele["tag"])] = float(N)
        momentos_base[str(ele["tag"])] = float(M_i)
        momentos_top[str(ele["tag"])] = float(M_j)

    cols = sorted(_elementos_por_tipo(data)["columna"], key=lambda e: e["tag"])
    viga = _elementos_por_tipo(data)["viga"][0]
    salida["axial_columna_barlovento"] = axiales[str(cols[0]["tag"])]
    salida["axial_columna_sotavento"] = axiales[str(cols[1]["tag"])]
    salida["axial_viga"] = axiales[str(viga["tag"])]
    salida["M_base_columna_barlovento"] = momentos_base[str(cols[0]["tag"])]
    salida["M_top_columna_barlovento"] = momentos_top[str(cols[0]["tag"])]
    return salida


def nodos_superiores(data):
    base = {int(t) for t in data["apoyos"]}
    return [t for t in sorted(int(t) for t in data["nodos"]) if t not in base]


def solucion_analitica(data):
    if data["nombre"] == "voladizo_3d":
        return solucion_voladizo(data)
    if data["nombre"] == "marco_3d":
        return solucion_marco(data)
    raise ValueError(f"Caso sin solucion analitica definida: {data['nombre']}")
