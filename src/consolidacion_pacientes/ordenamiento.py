"""Consolidación mediante ordenamiento estable por mezcla."""

from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from modelo import Resultado


T = TypeVar("T")
ResultadoNumerado = tuple[int, Resultado]


def consolidar_ordenamiento(
    resultados: Sequence[Resultado],
) -> list[Resultado]:
    """Conserva el resultado más reciente tras agrupar por paciente.

    El primer ordenamiento estable agrupa las claves sin perder el orden de
    llegada dentro de cada grupo. El segundo recupera el orden de primera
    aparición de los pacientes en la salida.
    """
    numerados: list[ResultadoNumerado] = list(enumerate(resultados))
    agrupados = _ordenar_merge(
        numerados,
        lambda elemento: elemento[1].clave_paciente,
    )
    seleccionados: list[ResultadoNumerado] = []
    posicion = 0

    while posicion < len(agrupados):
        primera_posicion, elegido = agrupados[posicion]
        clave = elegido.clave_paciente
        posicion += 1

        while (
            posicion < len(agrupados)
            and agrupados[posicion][1].clave_paciente == clave
        ):
            candidato = agrupados[posicion][1]
            if candidato.fecha_resultado > elegido.fecha_resultado:
                elegido = candidato
            posicion += 1

        seleccionados.append((primera_posicion, elegido))

    por_primera_aparicion = _ordenar_merge(
        seleccionados,
        lambda elemento: elemento[0],
    )
    return [resultado for _, resultado in por_primera_aparicion]


def _ordenar_merge(
    elementos: Sequence[T],
    clave: Callable[[T], Any],
) -> list[T]:
    """Retorna una copia ordenada de forma estable mediante merge sort."""
    if len(elementos) <= 1:
        return list(elementos)

    mitad = len(elementos) // 2
    izquierda = _ordenar_merge(elementos[:mitad], clave)
    derecha = _ordenar_merge(elementos[mitad:], clave)
    return _mezclar(izquierda, derecha, clave)


def _mezclar(
    izquierda: Sequence[T],
    derecha: Sequence[T],
    clave: Callable[[T], Any],
) -> list[T]:
    """Mezcla dos secuencias ordenadas y prioriza la izquierda en empates."""
    mezcla: list[T] = []
    indice_izquierdo = 0
    indice_derecho = 0

    while indice_izquierdo < len(izquierda) and indice_derecho < len(derecha):
        elemento_izquierdo = izquierda[indice_izquierdo]
        elemento_derecho = derecha[indice_derecho]

        if clave(elemento_izquierdo) <= clave(elemento_derecho):
            mezcla.append(elemento_izquierdo)
            indice_izquierdo += 1
        else:
            mezcla.append(elemento_derecho)
            indice_derecho += 1

    mezcla.extend(izquierda[indice_izquierdo:])
    mezcla.extend(derecha[indice_derecho:])
    return mezcla
