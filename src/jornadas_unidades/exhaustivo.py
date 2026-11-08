"""Solución exhaustiva para programar las jornadas de una unidad móvil."""

from itertools import product


# (inicio, fin, pacientes_alto_riesgo); inicio y fin están en minutos.
Jornada = tuple[int, int, int]


def _subconjunto_sin_cruces(jornadas: list[Jornada]) -> bool:
    """Indica si un subconjunto ordenado por inicio no tiene cruces.

    Dos jornadas que se tocan en un extremo se consideran compatibles.

    Args:
        jornadas: Jornadas ordenadas de menor a mayor hora de inicio.

    Returns:
        True si ninguna jornada empieza antes de que termine la anterior.
    """
    for posicion in range(1, len(jornadas)):
        fin_anterior = jornadas[posicion - 1][1]
        inicio_actual = jornadas[posicion][0]
        if inicio_actual < fin_anterior:
            return False
    return True


def seleccionar_exhaustivo(solicitudes: list[Jornada]) -> list[Jornada]:
    """Elige el mejor subconjunto de jornadas probando todas las opciones.

    La función se usa como referencia exacta para validar la programación
    dinámica en instancias pequeñas. Su costo es exponencial, por lo que no
    debe ejecutarse con el volumen real de solicitudes.

    Args:
        solicitudes: Solicitudes del mes de una subregión.

    Returns:
        Un subconjunto sin cruces que maximiza los pacientes de alto riesgo,
        ordenado por hora de inicio.
    """
    mejor: list[Jornada] = []
    mejor_total = 0
    cantidad = len(solicitudes)

    for decisiones in product((False, True), repeat=cantidad):
        candidatas = [
            solicitudes[indice]
            for indice in range(cantidad)
            if decisiones[indice]
        ]
        candidatas.sort(
            key=lambda jornada: (jornada[0], jornada[1], jornada[2])
        )
        if not _subconjunto_sin_cruces(candidatas):
            continue

        total = sum(jornada[2] for jornada in candidatas)
        if total > mejor_total:
            mejor = candidatas
            mejor_total = total

    return mejor
