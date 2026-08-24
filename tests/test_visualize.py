"""Tests de la visualizacion: los ejes locales dibujados deben coincidir
con la convencion de geomTransf Linear de OpenSees.

La figura es confiable si y solo si la funcion que calcula los ejes para
dibujarlos produce exactamente los ejes locales reales de cada elemento.
Estos tests fijan ese contrato numericamente.
"""

from pathlib import Path

import numpy as np
import pytest

from src.model import cargar_caso
from src.visualize import _ejes_locales

DATA = Path(__file__).resolve().parents[1] / "data"


def _triades(data):
    salida = {}
    for ele in data["elementos"]:
        pi = np.asarray(data["nodos"][str(ele["i"])], float)
        pj = np.asarray(data["nodos"][str(ele["j"])], float)
        vecxz = data["transformaciones"][ele["transf"]]["vecxz"]
        salida[ele["tag"]] = _ejes_locales(pi, pj, vecxz)
    return salida


def _es_triad_ortonormal_dextrorigida(x, y, z):
    for eje in (x, y, z):
        assert np.linalg.norm(eje) == pytest.approx(1.0, abs=1e-12)
    assert np.dot(x, y) == pytest.approx(0.0, abs=1e-12)
    assert np.dot(y, z) == pytest.approx(0.0, abs=1e-12)
    assert np.dot(x, z) == pytest.approx(0.0, abs=1e-12)
    # Regla de la mano derecha: x cruz y = z.
    np.testing.assert_allclose(np.cross(x, y), z, atol=1e-12)


def test_ejes_voladizo_coiniden_con_globales():
    """Viga sobre X con vecxz=(0,0,1): ejes locales = ejes globales."""
    data = cargar_caso(DATA / "voladizo.json")
    x, y, z = _triades(data)[1]
    np.testing.assert_allclose(x, [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(y, [0, 1, 0], atol=1e-12)
    np.testing.assert_allclose(z, [0, 0, 1], atol=1e-12)
    _es_triad_ortonormal_dextrorigida(x, y, z)


def test_ejes_marco_columna_y_viga():
    data = cargar_caso(DATA / "marco3d.json")
    triades = _triades(data)

    # Columna vertical (vecxz=(0,1,0)): local x sube por Z,
    # local y apunta a X global, local z a Y global.
    x, y, z = triades[11]
    np.testing.assert_allclose(x, [0, 0, 1], atol=1e-12)
    np.testing.assert_allclose(y, [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(z, [0, 1, 0], atol=1e-12)
    _es_triad_ortonormal_dextrorigida(x, y, z)

    # Viga horizontal: igual convencion que el voladizo.
    x, y, z = triades[21]
    np.testing.assert_allclose(x, [1, 0, 0], atol=1e-12)
    np.testing.assert_allclose(y, [0, 1, 0], atol=1e-12)
    np.testing.assert_allclose(z, [0, 0, 1], atol=1e-12)


def test_todas_las_triads_ortonomales_y_dextrorigidas():
    for nombre in ("voladizo.json", "marco3d.json"):
        for tag, (x, y, z) in _triades(cargar_caso(DATA / nombre)).items():
            _es_triad_ortonormal_dextrorigida(x, y, z)


def test_vecxz_paralelo_al_eje_rechazado():
    """Regla critica del tutorial: vecxz nunca paralelo al eje del elemento."""
    with pytest.raises(ValueError):
        _ejes_locales([0, 0, 0], [0, 0, 4], [0, 0, 1])


def test_figuras_generadas_existen():
    figs = Path(__file__).resolve().parents[1] / "results" / "figures"
    for nombre in ("voladizo_3d.png", "marco_3d.png"):
        archivo = figs / nombre
        assert archivo.exists()
        assert archivo.stat().st_size > 10_000
