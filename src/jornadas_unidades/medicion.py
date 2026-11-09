"""Medición reproducible de las estrategias para programar jornadas."""

import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from datos import generar_solicitudes
from estrategia import Jornada, seleccionar_jornadas
from exhaustivo import seleccionar_exhaustivo
from regla_actual import asignar_por_llegada, se_cruzan


Algoritmo = Callable[[list[Jornada]], list[Jornada]]


@dataclass
class FilaMedicion:
    """Resultados obtenidos para un tamaño de entrada."""

    n: int
    tiempo_dinamica: float
    tiempo_actual: float
    operaciones_dinamica: int
    operaciones_actual: int
    tiempo_exhaustiva: Optional[float] = None
    operaciones_exhaustiva: Optional[int] = None


def medir_tiempo(
    algoritmo: Algoritmo, solicitudes: list[Jornada], repeticiones: int
) -> float:
    """Mide el tiempo medio de un algoritmo sin incluir los datos.

    Args:
        algoritmo: Función que selecciona un subconjunto de jornadas.
        solicitudes: Instancia generada antes de iniciar el cronómetro.
        repeticiones: Número de ejecuciones usadas para promediar el ruido.

    Returns:
        El tiempo medio en segundos.

    Raises:
        ValueError: Si el número de repeticiones no es positivo.
    """
    if repeticiones <= 0:
        raise ValueError("Las repeticiones deben ser mayores que cero")

    total = 0.0
    for _ in range(repeticiones):
        inicio = perf_counter()
        algoritmo(solicitudes)
        total += perf_counter() - inicio
    return total / repeticiones


def medir_memoria_pico(
    algoritmo: Algoritmo, solicitudes: list[Jornada]
) -> int:
    """Mide las asignaciones adicionales máximas de una estrategia.

    La entrada se crea antes de iniciar el seguimiento y se ejecuta una vez el
    algoritmo para reducir el efecto de inicializaciones internas de Python.

    Args:
        algoritmo: Función que selecciona un subconjunto de jornadas.
        solicitudes: Instancia ya generada que se debe procesar.

    Returns:
        El pico de memoria adicional en bytes registrado por ``tracemalloc``.
    """
    algoritmo(solicitudes)
    tracemalloc.start()
    algoritmo(solicitudes)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return pico


def _ordenar_contando(jornadas: list[Jornada]) -> tuple[list[Jornada], int]:
    """Ordena por finalización con merge sort y cuenta comparaciones.

    Args:
        jornadas: Jornadas que se deben ordenar sin modificar la lista original.

    Returns:
        La copia ordenada y el número de comparaciones entre jornadas.
    """
    if len(jornadas) <= 1:
        return jornadas.copy(), 0

    mitad = len(jornadas) // 2
    izquierda, comparaciones_izquierda = _ordenar_contando(jornadas[:mitad])
    derecha, comparaciones_derecha = _ordenar_contando(jornadas[mitad:])
    mezcla: list[Jornada] = []
    comparaciones = comparaciones_izquierda + comparaciones_derecha
    indice_izquierdo = 0
    indice_derecho = 0

    while indice_izquierdo < len(izquierda) and indice_derecho < len(derecha):
        comparaciones += 1
        clave_izquierda = (
            izquierda[indice_izquierdo][1],
            izquierda[indice_izquierdo][0],
            izquierda[indice_izquierdo][2],
        )
        clave_derecha = (
            derecha[indice_derecho][1],
            derecha[indice_derecho][0],
            derecha[indice_derecho][2],
        )
        if clave_izquierda <= clave_derecha:
            mezcla.append(izquierda[indice_izquierdo])
            indice_izquierdo += 1
        else:
            mezcla.append(derecha[indice_derecho])
            indice_derecho += 1

    mezcla.extend(izquierda[indice_izquierdo:])
    mezcla.extend(derecha[indice_derecho:])
    return mezcla, comparaciones


def contar_operaciones_dinamica(solicitudes: list[Jornada]) -> int:
    """Cuenta comparaciones de ordenamiento, búsquedas y tabla dinámica.

    Args:
        solicitudes: Solicitudes de una subregión.

    Returns:
        Comparaciones realizadas por una versión instrumentada equivalente.
    """
    ordenadas, operaciones = _ordenar_contando(solicitudes)
    fines = [jornada[1] for jornada in ordenadas]

    for j, jornada in enumerate(ordenadas):
        bajo = 0
        alto = j
        while bajo < alto:
            operaciones += 1
            medio = (bajo + alto) // 2
            if fines[medio] <= jornada[0]:
                bajo = medio + 1
            else:
                alto = medio
        operaciones += 1  # comparación entre elegir y no elegir la jornada

    return operaciones


def contar_operaciones_actual(solicitudes: list[Jornada]) -> int:
    """Cuenta comparaciones de cruces de la asignación por llegada.

    Args:
        solicitudes: Solicitudes en su orden de llegada.

    Returns:
        Cantidad de comparaciones entre parejas de jornadas.
    """
    aceptadas: list[Jornada] = []
    operaciones = 0
    for solicitud in solicitudes:
        conflicto = False
        for aceptada in aceptadas:
            operaciones += 1
            if se_cruzan(solicitud, aceptada):
                conflicto = True
                break
        if not conflicto:
            aceptadas.append(solicitud)
    return operaciones


def _total_pacientes(jornadas: list[Jornada]) -> int:
    """Suma los pacientes atendidos por unas jornadas.

    Args:
        jornadas: Jornadas seleccionadas por una estrategia.

    Returns:
        La cantidad total de pacientes de alto riesgo atendidos.
    """
    return sum(jornada[2] for jornada in jornadas)


def medir_series(
    tamanos_comunes: list[int],
    tamanos_grandes: list[int],
    repeticiones: int = 5,
    semilla: int = 2026,
) -> list[FilaMedicion]:
    """Mide las estrategias con instancias iguales para cada tamaño.

    Args:
        tamanos_comunes: Tamaños pequeños donde corre la exhaustiva.
        tamanos_grandes: Tamaños adicionales para las soluciones eficientes.
        repeticiones: Ejecuciones cronometradas por algoritmo y tamaño.
        semilla: Base usada para generar instancias reproducibles.

    Returns:
        Una fila con tiempos y operaciones por cada tamaño solicitado.
    """
    filas: list[FilaMedicion] = []
    comunes = set(tamanos_comunes)
    for n in tamanos_comunes + tamanos_grandes:
        solicitudes = generar_solicitudes(n, semilla + n)
        dinamica = seleccionar_jornadas(solicitudes)
        tiempo_dinamica = medir_tiempo(
            seleccionar_jornadas, solicitudes, repeticiones
        )
        tiempo_actual = medir_tiempo(
            asignar_por_llegada, solicitudes, repeticiones
        )
        fila = FilaMedicion(
            n=n,
            tiempo_dinamica=tiempo_dinamica,
            tiempo_actual=tiempo_actual,
            operaciones_dinamica=contar_operaciones_dinamica(solicitudes),
            operaciones_actual=contar_operaciones_actual(solicitudes),
        )

        if n in comunes:
            exhaustiva = seleccionar_exhaustivo(solicitudes)
            assert _total_pacientes(dinamica) == _total_pacientes(exhaustiva)
            fila.tiempo_exhaustiva = medir_tiempo(
                seleccionar_exhaustivo, solicitudes, repeticiones
            )
            fila.operaciones_exhaustiva = 2**n
        filas.append(fila)
    return filas


def imprimir_resumen(filas: list[FilaMedicion]) -> None:
    """Imprime una tabla compacta de las mediciones.

    Args:
        filas: Resultados devueltos por ``medir_series``.
    """
    encabezado = "n | dinámica (ms) | actual (ms) | exhaustiva (ms)"
    print(encabezado)
    print("-" * len(encabezado))
    for fila in filas:
        exhaustiva = "—"
        if fila.tiempo_exhaustiva is not None:
            exhaustiva = f"{fila.tiempo_exhaustiva * 1000:.3f}"
        print(
            f"{fila.n} | {fila.tiempo_dinamica * 1000:.3f} | "
            f"{fila.tiempo_actual * 1000:.3f} | {exhaustiva}"
        )


def graficar_tiempos(
    filas: list[FilaMedicion], directorio: Path
) -> Path:
    """Grafica los tiempos comunes y la escala de las soluciones prácticas.

    Args:
        filas: Resultados devueltos por ``medir_series``.
        directorio: Carpeta donde se debe guardar la imagen.

    Returns:
        La ruta del archivo PNG generado.
    """
    comunes = [fila for fila in filas if fila.tiempo_exhaustiva is not None]
    figura, ejes = plt.subplots(
        1, 2, figsize=(12, 4.8), layout="constrained"
    )

    ejes[0].plot(
        [fila.n for fila in comunes],
        [fila.tiempo_dinamica * 1000 for fila in comunes],
        "o-",
        label="Programación dinámica",
    )
    ejes[0].plot(
        [fila.n for fila in comunes],
        [fila.tiempo_actual * 1000 for fila in comunes],
        "s-",
        label="Orden de llegada",
    )
    ejes[0].plot(
        [fila.n for fila in comunes],
        [fila.tiempo_exhaustiva * 1000 for fila in comunes],
        "^-",
        label="Exhaustiva",
    )
    ejes[0].set_yscale("log")
    ejes[0].set_title("Tres estrategias en tamaños pequeños")
    ejes[0].set_ylabel("Tiempo medio (ms, escala logarítmica)")

    ejes[1].plot(
        [fila.n for fila in filas],
        [fila.tiempo_dinamica * 1000 for fila in filas],
        "o-",
        label="Programación dinámica",
    )
    ejes[1].plot(
        [fila.n for fila in filas],
        [fila.tiempo_actual * 1000 for fila in filas],
        "s-",
        label="Orden de llegada",
    )
    ejes[1].set_title("Estrategias prácticas en tamaños grandes")
    ejes[1].set_ylabel("Tiempo medio (ms)")

    for eje in ejes:
        eje.set_xlabel("Número de solicitudes n")
        eje.grid(True, alpha=0.3)
        eje.legend()
    figura.suptitle("Programación de jornadas: tiempo frente al tamaño")
    directorio.mkdir(parents=True, exist_ok=True)
    archivo = directorio / "tiempo_vs_n.png"
    figura.savefig(archivo, dpi=150)
    plt.close(figura)
    return archivo


def graficar_operaciones(
    filas: list[FilaMedicion], directorio: Path
) -> Path:
    """Grafica las operaciones contadas para las tres estrategias.

    Args:
        filas: Resultados devueltos por ``medir_series``.
        directorio: Carpeta donde se debe guardar la imagen.

    Returns:
        La ruta del archivo PNG generado.
    """
    comunes = [
        fila for fila in filas if fila.operaciones_exhaustiva is not None
    ]
    figura, ejes = plt.subplots(
        1, 2, figsize=(12, 4.8), layout="constrained"
    )

    ejes[0].plot(
        [fila.n for fila in comunes],
        [fila.operaciones_dinamica for fila in comunes],
        "o-",
        label="Programación dinámica",
    )
    ejes[0].plot(
        [fila.n for fila in comunes],
        [fila.operaciones_actual for fila in comunes],
        "s-",
        label="Orden de llegada",
    )
    ejes[0].plot(
        [fila.n for fila in comunes],
        [fila.operaciones_exhaustiva for fila in comunes],
        "^-",
        label="Exhaustiva",
    )
    ejes[0].set_yscale("log")
    ejes[0].set_title("Tres estrategias en tamaños pequeños")
    ejes[0].set_ylabel("Operaciones (escala logarítmica)")

    ejes[1].plot(
        [fila.n for fila in filas],
        [fila.operaciones_dinamica for fila in filas],
        "o-",
        label="Programación dinámica",
    )
    ejes[1].plot(
        [fila.n for fila in filas],
        [fila.operaciones_actual for fila in filas],
        "s-",
        label="Orden de llegada",
    )
    ejes[1].set_title("Estrategias prácticas en tamaños grandes")
    ejes[1].set_ylabel("Número de operaciones")

    for eje in ejes:
        eje.set_xlabel("Número de solicitudes n")
        eje.grid(True, alpha=0.3)
        eje.legend()
    figura.suptitle("Programación de jornadas: operaciones frente al tamaño")
    directorio.mkdir(parents=True, exist_ok=True)
    archivo = directorio / "operaciones_vs_n.png"
    figura.savefig(archivo, dpi=150)
    plt.close(figura)
    return archivo


if __name__ == "__main__":
    resultados = medir_series(
        tamanos_comunes=[4, 6, 8, 10, 12, 14],
        tamanos_grandes=[20, 40, 80, 120, 240, 480],
    )
    imprimir_resumen(resultados)
    destino = Path("graficas/jornadas_unidades")
    print(f"Gráfica guardada en {graficar_tiempos(resultados, destino)}")
    print(f"Gráfica guardada en {graficar_operaciones(resultados, destino)}")
    for cantidad in (120, 480):
        instancia = generar_solicitudes(cantidad, 2026 + cantidad)
        memoria = medir_memoria_pico(seleccionar_jornadas, instancia)
        print(f"Memoria adicional para n={cantidad}: {memoria / 1024:.1f} KiB")
