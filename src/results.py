"""Extraccion de resultados del dominio OpenSees.

Contrato de fuerzas locales (validado numericamente en tests):
ops.eleResponse(tag, "localForce") retorna 12 componentes en ejes locales:
[N_i, Vy_i, Vz_i, T_i, My_i, Mz_i, N_j, Vy_j, Vz_j, T_j, My_j, Mz_j]
- N: fuerza axial (+ tension) a lo largo del eje local x.
- Vy, Vz: cortes segun ejes locales y, z.
- T: torsion sobre eje local x.
- My, Mz: momentos de extremo sobre ejes locales y, z, evaluados en cada nodo.
"""

import openseespy.opensees as ops

COMPONENTES_LOCAL_FORCE = [
    "N_i", "Vy_i", "Vz_i", "T_i", "My_i", "Mz_i",
    "N_j", "Vy_j", "Vz_j", "T_j", "My_j", "Mz_j",
]


def extraer_desplazamientos(tags_nodos):
    """{tag: [uX, uY, uZ, rX, rY, rZ]} con claves str para JSON."""
    return {str(tag): list(ops.nodeDisp(tag)) for tag in tags_nodos}


def extraer_reacciones(tags_nodos):
    """{tag: [RX, RY, RZ, MX, MY, MZ]}. Requiere llamar ops.reactions()."""
    ops.reactions()
    return {str(tag): list(ops.nodeReaction(tag)) for tag in tags_nodos}


def extraer_fuerzas_locales(tags_elementos):
    """{tag: dict componente -> valor} segun COMPONENTES_LOCAL_FORCE."""
    salida = {}
    for tag in tags_elementos:
        valores = ops.eleResponse(tag, "localForce")
        salida[str(tag)] = dict(zip(COMPONENTES_LOCAL_FORCE, valores))
    return salida
