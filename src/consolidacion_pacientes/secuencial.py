"""Consolidación mediante búsqueda secuencial en una lista."""

from collections.abc import Sequence

from modelo import Resultado


def consolidar_secuencial(resultados: Sequence[Resultado]) -> list[Resultado]:
    """Conserva el resultado más reciente de cada paciente.

    La lista consolidada mantiene el orden en que apareció por primera vez cada
    paciente. Ante dos fechas iguales se conserva el primer resultado recibido.
    La entrada y sus registros no se modifican.
    """
    consolidados: list[Resultado] = []

    for resultado in resultados:
        for posicion, guardado in enumerate(consolidados):
            if guardado.clave_paciente != resultado.clave_paciente:
                continue

            if resultado.fecha_resultado > guardado.fecha_resultado:
                consolidados[posicion] = resultado
            break
        else:
            consolidados.append(resultado)

    return consolidados
