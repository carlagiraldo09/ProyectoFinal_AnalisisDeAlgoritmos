"""Regla actual para asignar jornadas de una unidad móvil."""


# (inicio, fin, pacientes_alto_riesgo); inicio y fin están en minutos.
Jornada = tuple[int, int, int]


def se_cruzan(primera: Jornada, segunda: Jornada) -> bool:
    """Indica si dos jornadas ocupan la unidad móvil al mismo tiempo.

    Los intervalos se interpretan como ``[inicio, fin)``. Por tanto, una
    jornada que empieza exactamente cuando otra termina es compatible.

    Args:
        primera: Primera jornada que se compara.
        segunda: Segunda jornada que se compara.

    Returns:
        True si las jornadas se superponen; False en caso contrario.
    """
    return primera[0] < segunda[1] and segunda[0] < primera[1]


def hay_cruce(jornadas: list[Jornada]) -> bool:
    """Indica si alguna pareja de jornadas se cruza.

    Args:
        jornadas: Jornadas que se deben revisar.

    Returns:
        True si existe al menos una pareja superpuesta.
    """
    for primera in range(len(jornadas)):
        for segunda in range(primera + 1, len(jornadas)):
            if se_cruzan(jornadas[primera], jornadas[segunda]):
                return True
    return False


def asignar_por_llegada(solicitudes: list[Jornada]) -> list[Jornada]:
    """Reproduce el procedimiento actual de la organización.

    Las solicitudes se revisan en el orden recibido. Cada una se acepta si
    no se cruza con ninguna jornada aceptada previamente. La función no
    modifica la lista de entrada.

    Args:
        solicitudes: Solicitudes en el orden en que llegaron.

    Returns:
        Las jornadas aceptadas, conservando su orden de llegada.
    """
    aceptadas: list[Jornada] = []
    for solicitud in solicitudes:
        tiene_conflicto = any(
            se_cruzan(solicitud, aceptada) for aceptada in aceptadas
        )
        if not tiene_conflicto:
            aceptadas.append(solicitud)
    return aceptadas
