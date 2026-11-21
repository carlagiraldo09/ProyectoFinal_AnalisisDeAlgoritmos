"""Genera las gráficas del experimento de consolidación."""

import csv
from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]
RUTA_DATOS = RAIZ_REPOSITORIO / "resultados" / "consolidacion.csv"
CARPETA_GRAFICAS = RAIZ_REPOSITORIO / "graficas" / "consolidacion_pacientes"

ESTILOS = {
    "secuencial": ("Búsqueda secuencial", "#D55E00", "o"),
    "ordenamiento": ("Merge sort estable", "#0072B2", "s"),
    "hash": ("Tabla hash", "#009E73", "^"),
}


def cargar_mediciones(ruta: Path = RUTA_DATOS) -> list[dict[str, object]]:
    """Lee el CSV y convierte sus columnas numéricas."""
    mediciones: list[dict[str, object]] = []
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            mediciones.append(
                {
                    "cantidad": int(fila["cantidad"]),
                    "estrategia": fila["estrategia"],
                    "tiempo_ms": float(fila["tiempo_ms"]),
                    "comparaciones": int(fila["comparaciones"]),
                    "memoria_pico_kib": float(fila["memoria_pico_kib"]),
                }
            )
    return mediciones


def generar_graficas(
    mediciones: Sequence[dict[str, object]],
    carpeta: Path = CARPETA_GRAFICAS,
) -> None:
    """Crea gráficas de tiempo, comparaciones y memoria máxima."""
    carpeta.mkdir(parents=True, exist_ok=True)
    _graficar_metrica(
        mediciones,
        "tiempo_ms",
        "Tiempo promedio (ms)",
        "Tiempo de consolidación",
        carpeta / "tiempo_vs_n.png",
    )
    _graficar_metrica(
        mediciones,
        "comparaciones",
        "Comparaciones",
        "Comparaciones de claves, fechas y posiciones",
        carpeta / "comparaciones_vs_n.png",
    )
    _graficar_metrica(
        mediciones,
        "memoria_pico_kib",
        "Memoria adicional máxima (KiB)",
        "Memoria máxima durante la consolidación",
        carpeta / "memoria_vs_n.png",
    )


def _graficar_metrica(
    mediciones: Sequence[dict[str, object]],
    columna: str,
    etiqueta_y: str,
    titulo: str,
    ruta_salida: Path,
) -> None:
    """Grafica una columna para cada estrategia en escalas logarítmicas."""
    plt.style.use("seaborn-v0_8-whitegrid")
    figura, eje = plt.subplots(figsize=(9, 5.5))

    for estrategia, (etiqueta, color, marcador) in ESTILOS.items():
        filas = [
            fila for fila in mediciones if fila["estrategia"] == estrategia
        ]
        cantidades = [int(fila["cantidad"]) for fila in filas]
        valores = [float(fila[columna]) for fila in filas]
        eje.plot(
            cantidades,
            valores,
            label=etiqueta,
            color=color,
            marker=marcador,
            linewidth=2,
            markersize=5,
        )

    eje.set_xscale("log")
    eje.set_yscale("log")
    eje.set_xlabel("Cantidad de resultados (n)")
    eje.set_ylabel(etiqueta_y)
    eje.set_title(titulo)
    eje.legend(title="Estrategia")
    eje.grid(True, which="both", alpha=0.25)
    figura.text(
        0.99,
        0.01,
        "Datos sintéticos con 12 % de registros repetidos",
        ha="right",
        fontsize=8,
        color="#555555",
    )
    figura.tight_layout(rect=(0, 0.03, 1, 1))
    figura.savefig(ruta_salida, dpi=200, bbox_inches="tight")
    plt.close(figura)


if __name__ == "__main__":
    generar_graficas(cargar_mediciones())
    print(f"Gráficas guardadas en {CARPETA_GRAFICAS}")
