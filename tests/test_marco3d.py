"""Tests del benchmark P1L1: caso marco 3D minimo."""

from pathlib import Path

import pytest

from src.reference import solucion_analitica
from src.run_benchmark import ejecutar_caso

RUTA_CASO = Path(__file__).resolve().parents[1] / "data" / "marco3d.json"


@pytest.fixture(scope="module")
def salida():
    return ejecutar_caso(RUTA_CASO)


def test_todas_las_verificaciones_pasan(salida):
    _, resultados, _ = salida
    assert resultados["todos_pasaron"]


def test_chequeos_minimos_del_enunciado(salida):
    """El enunciado exige: suma cargas, suma reacciones, desplazamiento,
    fuerza axial y momento de extremo."""
    _, _, checks = salida
    por_id = {c["id"]: c for c in checks}
    for id_esperado in (
        "equilibrio_FX",
        "equilibrio_FZ",
        "deriva_ux_nodo3",
        "axial_columna_barlovento",
        "momento_base_columna",
    ):
        assert id_esperado in por_id
        assert por_id[id_esperado]["pasa"], f"Falla chequeo {id_esperado}"


def test_axiales_contra_portico_plano(salida):
    """Axiales de columnas contra la solucion independiente de portico plano."""
    data, resultados, _ = salida
    s = solucion_analitica(data)
    fuerzas = resultados["fuerzas_locales"]
    # Tension positiva: en localForce corresponde a N_j (contrato validado).
    assert fuerzas["11"]["N_j"] == pytest.approx(
        s["axial_columna_barlovento"], rel=1e-9
    )
    assert fuerzas["12"]["N_j"] == pytest.approx(
        s["axial_columna_sotavento"], rel=1e-9
    )
    # Equilibrio vertical interno: las axiales suman la carga vertical aplicada.
    suma = fuerzas["11"]["N_j"] + fuerzas["12"]["N_j"]
    assert suma == pytest.approx(-40.0, abs=1e-8)


def test_deriva_simetrica_en_ambos_nodos_superiores(salida):
    _, resultados, _ = salida
    ux3 = resultados["desplazamientos"]["3"][0]
    ux4 = resultados["desplazamientos"]["4"][0]
    assert ux3 == pytest.approx(ux4, rel=1e-12)
