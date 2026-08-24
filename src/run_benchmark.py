"""Script reproducible del benchmark P1L1.

Uso:
    python -m src.run_benchmark --caso data/voladizo.json
    python -m src.run_benchmark --caso data/marco3d.json

Ejecuta: construccion -> analisis -> extraccion -> verificacion ->
resultados JSON + figura. Retorna codigo de salida 1 si algun chequeo falla.
"""

import argparse
import json
from pathlib import Path

from src.analysis import ejecutar_analisis
from src.model import construir_modelo, cargar_caso
from src.results import (
    extraer_desplazamientos,
    extraer_fuerzas_locales,
    extraer_reacciones,
)
from src.verify import verificar_caso
from src.visualize import graficar_caso


def ejecutar_caso(ruta_datos, dir_resultados=None):
    """Pipeline completo en memoria. Retorna (data, resultados, checks)."""
    data = cargar_caso(ruta_datos)

    construir_modelo(data)
    ejecutar_analisis(data["nombre"])

    tags_nodos = [int(t) for t in data["nodos"]]
    tags_elementos = [int(e["tag"]) for e in data["elementos"]]

    desplazamientos = extraer_desplazamientos(tags_nodos)
    reacciones = extraer_reacciones(tags_nodos)
    fuerzas_locales = extraer_fuerzas_locales(tags_elementos)

    checks = verificar_caso(data, desplazamientos, reacciones, fuerzas_locales)

    resultados = {
        "caso": data["nombre"],
        "unidades": {"longitud": "m", "fuerza": "kN", "momento": "kN*m"},
        "desplazamientos": desplazamientos,
        "reacciones": reacciones,
        "fuerzas_locales": fuerzas_locales,
        "verificaciones": checks,
        "todos_pasaron": all(c["pasa"] for c in checks),
    }
    return data, resultados, checks


def guardar_resultados(resultados, ruta_json):
    ruta_json.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Benchmark 3D OpenSees (P1L1)")
    parser.add_argument(
        "--caso",
        default="data/voladizo.json",
        help="Ruta al JSON del caso (default: data/voladizo.json)",
    )
    parser.add_argument(
        "--dir-resultados",
        default="results",
        help="Directorio de salida (default: results)",
    )
    args = parser.parse_args()

    dir_resultados = Path(args.dir_resultados)
    fig_dir = dir_resultados / "figures"

    data, resultados, checks = ejecutar_caso(args.caso)

    print(f"\nCaso: {data['nombre']}")
    print(f"{'Chequeo':<32} {'OpenSees':>14} {'Referencia':>14} {'Error':>10}  OK?")
    for c in checks:
        valor_ops = c["valor_opensees"]
        valor_ref = c["valor_referencia"]
        if "error_rel" in c and c.get("tolerancia_rel"):
            medida = f"rel={c['error_rel']:.2e}"
        else:
            medida = f"|err|={c['error_abs']:.2e}"
        print(
            f"{c['id']:<32} {valor_ops:>14.6f} {valor_ref:>14.6f} {medida:>10}"
            f"  {'SI' if c['pasa'] else 'NO'}"
        )

    guardar_resultados(resultados, dir_resultados / f"{data['nombre']}_verificacion.json")
    graficar_caso(
        data,
        desplazamientos=resultados["desplazamientos"],
        ruta_salida=str(fig_dir / f"{data['nombre']}.png"),
    )
    print(f"\nResultados: {dir_resultados / (data['nombre'] + '_verificacion.json')}")
    print(f"Figura:     {fig_dir / (data['nombre'] + '.png')}")

    if not resultados["todos_pasaron"]:
        raise SystemExit("FALLO: al menos una verificacion no paso")


if __name__ == "__main__":
    main()
