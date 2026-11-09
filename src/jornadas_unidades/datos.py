"""Generación reproducible de solicitudes de jornadas móviles."""

import random

from estrategia import Jornada


def generar_solicitudes(cantidad: int, semilla: int) -> list[Jornada]:
    """Genera solicitudes sintéticas con una densidad de cruces estable.

    El horizonte crece junto con la cantidad de solicitudes para que aumentar
    ``n`` no produzca artificialmente un escenario donde todas se crucen. Los
    horarios se expresan en minutos desde el inicio del periodo.

    Args:
        cantidad: Número de solicitudes que se deben generar.
        semilla: Semilla fija para reproducir exactamente la instancia.

    Returns:
        Una lista de jornadas ``(inicio, fin, pacientes_alto_riesgo)``.

    Raises:
        ValueError: Si la cantidad solicitada es negativa.
    """
    if cantidad < 0:
        raise ValueError("La cantidad de solicitudes no puede ser negativa")

    azar = random.Random(semilla)
    horizonte = max(cantidad, 1) * 180
    solicitudes: list[Jornada] = []
    for _ in range(cantidad):
        inicio = azar.randrange(0, horizonte, 15)
        duracion = azar.randrange(60, 6 * 60 + 15, 15)
        pacientes = azar.randint(5, 150)
        solicitudes.append((inicio, inicio + duracion, pacientes))
    return solicitudes
