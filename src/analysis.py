"""Configuracion y ejecucion del analisis estatico lineal."""

import openseespy.opensees as ops


def configurar_analisis():
    ops.constraints("Plain")
    ops.numberer("RCM")
    ops.system("BandGeneral")
    ops.algorithm("Linear")
    ops.integrator("LoadControl", 1.0)
    ops.analysis("Static")


def ejecutar_analisis(nombre_caso=""):
    """Ejecuta 1 paso estatico. Retorna True si termino correctamente.

    Nota: analyze() == 0 significa que OpenSees resolvio el problema
    numerico; NO garantiza que el modelo represente bien la estructura.
    La correccion fisica se verifica aparte (src/verify.py).
    """
    configurar_analisis()
    ok = ops.analyze(1)
    if ok != 0:
        raise RuntimeError(f"El analisis OpenSees fallo para el caso {nombre_caso}")
    return True
