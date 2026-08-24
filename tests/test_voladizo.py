"""Tests del benchmark P1L1: caso voladizo 3D (tutorial Semana 1)."""

from pathlib import Path

import pytest

from src.run_benchmark import ejecutar_caso

RUTA_CASO = Path(__file__).resolve().parents[1] / "data" / "voladizo.json"


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
        "desplazamiento_punta_uz",
        "reaccion_Rz_apoyo",
        "axial_viga",
        "momento_extremo_empotrado",
    ):
        assert id_esperado in por_id
        assert por_id[id_esperado]["pasa"], f"Falla chequeo {id_esperado}"


def test_desplazamiento_valor_referencia(salida):
    """delta = P L^3/(3 E Iy) = 10*27/(3*25e6*0.003125) = 1.152e-3 m."""
    _, resultados, _ = salida
    uz = resultados["desplazamientos"]["2"][2]
    assert abs(uz) == pytest.approx(1.152e-3, rel=1e-10)


def test_reaccion_Rz_y_momento_empotramiento(salida):
    _, resultados, _ = salida
    Rz = resultados["reacciones"]["1"][2]
    My_i = resultados["fuerzas_locales"]["1"]["My_i"]
    assert Rz == pytest.approx(10.0, rel=1e-10)
    assert abs(My_i) == pytest.approx(30.0, rel=1e-9)


def test_contrato_local_force_tiene_12_componentes(salida):
    _, resultados, _ = salida
    fuerzas = resultados["fuerzas_locales"]["1"]
    assert len(fuerzas) == 12
