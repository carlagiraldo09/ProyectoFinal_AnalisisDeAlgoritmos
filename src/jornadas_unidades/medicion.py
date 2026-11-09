"""Medición reproducible de las estrategias para programar jornadas."""

from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Optional

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


def _ordenar_contando(jornadas: list[Jornada]) -> tuple[list[Jornada], int]:
    """Ordena por finalización con merge sort y cuenta comparaciones."""
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
    """Suma los pacientes atendidos por unas jornadas."""
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


if __name__ == "__main__":
    resultados = medir_series(
        tamanos_comunes=[4, 6, 8, 10, 12, 14],
        tamanos_grandes=[20, 40, 80, 120, 240, 480],
    )
    imprimir_resumen(resultados)
