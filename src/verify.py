"""Verificaciones cuantitativas del benchmark.

Genera una lista de chequeos comparando la respuesta OpenSees contra
soluciones analiticas independientes (src/reference.py) y contra el
equilibrio global. Cada chequeo se guarda con su error y su veredicto.
"""

from src.reference import solucion_analitica

TOL_EQUILIBRIO_ABS = 1.0e-8


def _chequeo(id_chequeo, descripcion, valor_ops, valor_ref, tol_rel=None):
    if valor_ref == 0.0 or tol_rel is None:
        error = abs(valor_ops - valor_ref)
        return {
            "id": id_chequeo,
            "descripcion": descripcion,
            "valor_opensees": valor_ops,
            "valor_referencia": valor_ref,
            "error_abs": error,
            "tolerancia_abs": TOL_EQUILIBRIO_ABS,
            "pasa": bool(error <= TOL_EQUILIBRIO_ABS),
        }
    error_rel = abs(valor_ops - valor_ref) / abs(valor_ref)
    return {
        "id": id_chequeo,
        "descripcion": descripcion,
        "valor_opensees": valor_ops,
        "valor_referencia": valor_ref,
        "error_abs": abs(valor_ops - valor_ref),
        "error_rel": error_rel,
        "tolerancia_rel": tol_rel,
        "pasa": bool(error_rel <= tol_rel),
    }


def verificar_equilibrio(data, reacciones):
    """suma(cargas aplicadas) + suma(reacciones) ~ 0 en cada traslacion."""
    aplicadas = [sum(c["fxyz"][dof] for c in data["cargas_nodales"]) for dof in range(3)]
    reaccion_total = [
        sum(reacciones[str(tag)][dof] for tag in data["nodos"]) for dof in range(3)
    ]
    nombres = ["FX", "FY", "FZ"]
    return [
        _chequeo(
            f"equilibrio_{nombre}",
            f"Suma de cargas + reacciones en {nombre} debe ser cero",
            aplicadas[dof] + reaccion_total[dof],
            0.0,
        )
        for dof, nombre in enumerate(nombres)
    ]


def _checks_voladizo(s, desplazamientos, reacciones, fuerzas_locales):
    checks = []
    uz = desplazamientos["2"][2]
    checks.append(
        _chequeo(
            "desplazamiento_punta_uz",
            "|uz| de la punta vs Euler-Bernoulli P L^3/(3 E Iy)",
            abs(uz),
            s["delta_punta"],
            1.0e-10,
        )
    )
    checks.append(
        _chequeo(
            "reaccion_Rz_apoyo",
            "Reaccion vertical del empotramiento equilibra P",
            reacciones["1"][2],
            s["Rz_apoyo"],
            1.0e-10,
        )
    )
    fuerza = fuerzas_locales["1"]
    checks.append(
        _chequeo("axial_viga", "Fuerza axial de la viga debe ser nula", fuerza["N_i"], 0.0)
    )
    checks.append(
        _chequeo(
            "momento_extremo_empotrado",
            "Momento de extremo en el empotramiento (magnitud |My_i|) vs P L",
            abs(fuerza["My_i"]),
            s["M_empotramiento"],
            1.0e-9,
        )
    )
    return checks


def _checks_marco(s, data, desplazamientos, fuerzas_locales):
    por_tipo = {}
    for ele in data["elementos"]:
        por_tipo.setdefault(ele["tipo"], []).append(str(ele["tag"]))
    tags_cols = sorted(por_tipo["columna"], key=int)
    col_barlovento = tags_cols[0]
    col_sotavento = tags_cols[1]
    viga = por_tipo["viga"][0]

    checks = []
    for nodo in ("3", "4"):
        checks.append(
            _chequeo(
                f"deriva_ux_nodo{nodo}",
                "Desplazamiento lateral superior vs pendiente-desplazamiento",
                desplazamientos[nodo][0],
                s["deriva"],
                1.0e-9,
            )
        )
    checks.append(
        _chequeo(
            "axial_columna_barlovento",
            "Axial columna barlovento (tension positiva) vs portico plano",
            fuerzas_locales[col_barlovento]["N_j"],
            s["axial_columna_barlovento"],
            1.0e-9,
        )
    )
    checks.append(
        _chequeo(
            "axial_columna_sotavento",
            "Axial columna sotavento (tension positiva) vs portico plano",
            fuerzas_locales[col_sotavento]["N_j"],
            s["axial_columna_sotavento"],
            1.0e-9,
        )
    )
    checks.append(
        _chequeo(
            "axial_viga",
            "Fuerza axial de la viga debe ser nula (cargas laterales simetricas)",
            fuerzas_locales[viga]["N_i"],
            s["axial_viga"],
        )
    )
    checks.append(
        _chequeo(
            "momento_base_columna",
            "Momento de extremo en base de columna (magnitud |Mz_i|)",
            abs(fuerzas_locales[col_barlovento]["Mz_i"]),
            abs(s["M_base_columna_barlovento"]),
            1.0e-9,
        )
    )
    checks.append(
        _chequeo(
            "momento_top_columna",
            "Momento de extremo superior de columna (magnitud |Mz_j|)",
            abs(fuerzas_locales[col_barlovento]["Mz_j"]),
            abs(s["M_top_columna_barlovento"]),
            1.0e-9,
        )
    )
    momento_nodo3 = (
        fuerzas_locales[col_barlovento]["Mz_j"] + fuerzas_locales[viga]["My_i"]
    )
    checks.append(
        _chequeo(
            "equilibrio_rotacional_nodo3",
            "Suma de momentos de extremo en el nodo 3 (columna + viga) debe ser nula",
            momento_nodo3,
            0.0,
        )
    )
    return checks


def verificar_caso(data, desplazamientos, reacciones, fuerzas_locales):
    """Retorna la lista completa de chequeos del caso."""
    checks = verificar_equilibrio(data, reacciones)
    s = solucion_analitica(data)
    if data["nombre"] == "voladizo_3d":
        checks += _checks_voladizo(s, desplazamientos, reacciones, fuerzas_locales)
    elif data["nombre"] == "marco_3d":
        checks += _checks_marco(s, data, desplazamientos, fuerzas_locales)
    else:
        raise ValueError(f"Caso sin verificaciones definidas: {data['nombre']}")
    return checks
