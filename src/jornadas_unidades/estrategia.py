"""Núcleo de programación dinámica para las jornadas de una unidad móvil."""

from bisect import bisect_right


# (inicio, fin, pacientes_alto_riesgo); inicio y fin están en minutos.
Jornada = tuple[int, int, int]


def ordenar_por_fin(solicitudes: list[Jornada]) -> list[Jornada]:
    """Ordena una copia de las solicitudes por su hora de finalización.

    Args:
        solicitudes: Jornadas solicitadas para una subregión.

    Returns:
        Una lista nueva ordenada por fin, inicio y cantidad de pacientes.
    """
    return sorted(solicitudes, key=lambda jornada: (jornada[1], jornada[0], jornada[2]))


def calcular_compatibles_anteriores(ordenadas: list[Jornada]) -> list[int]:
    """Calcula cuántas jornadas anteriores son compatibles con cada jornada.

    Dos jornadas que se tocan en un extremo se consideran compatibles. La
    posición ``j`` del resultado usa índices de programación dinámica: el
    valor cero representa el caso base y las jornadas empiezan en uno.

    Args:
        ordenadas: Jornadas ordenadas de menor a mayor hora de finalización.

    Returns:
        La lista ``p``, donde ``p[j]`` es la cantidad de jornadas anteriores
        que terminan antes o exactamente cuando empieza la jornada ``j``.
    """
    fines = [jornada[1] for jornada in ordenadas]
    compatibles = [0] * (len(ordenadas) + 1)

    for j in range(1, len(ordenadas) + 1):
        inicio = ordenadas[j - 1][0]
        compatibles[j] = bisect_right(fines, inicio, 0, j - 1)

    return compatibles


def calcular_tabla_optima(
    ordenadas: list[Jornada], compatibles: list[int]
) -> list[int]:
    """Calcula el máximo de pacientes atendidos para cada prefijo.

    La recurrencia compara excluir la jornada ``j`` con incluirla y sumar su
    cantidad de pacientes al mejor resultado compatible anterior.

    Args:
        ordenadas: Jornadas ordenadas de menor a mayor hora de finalización.
        compatibles: Lista ``p`` calculada para las mismas jornadas.

    Returns:
        La tabla ``M``; ``M[j]`` es el máximo de pacientes que pueden
        atenderse usando únicamente las primeras ``j`` jornadas.

    Raises:
        ValueError: Si la lista de compatibilidades no corresponde al tamaño
            de las jornadas ordenadas.
    """
    if len(compatibles) != len(ordenadas) + 1:
        raise ValueError("La tabla de compatibilidades tiene un tamaño inválido")

    mejor = [0] * (len(ordenadas) + 1)
    for j in range(1, len(ordenadas) + 1):
        no_elegir = mejor[j - 1]
        pacientes = ordenadas[j - 1][2]
        elegir = pacientes + mejor[compatibles[j]]
        mejor[j] = max(no_elegir, elegir)

    return mejor


def calcular_valor_optimo(solicitudes: list[Jornada]) -> int:
    """Calcula el máximo de pacientes sin modificar las solicitudes.

    Args:
        solicitudes: Jornadas solicitadas para una subregión.

    Returns:
        La cantidad máxima de pacientes de alto riesgo que puede atender la
        unidad móvil sin programar jornadas que se crucen.
    """
    ordenadas = ordenar_por_fin(solicitudes)
    compatibles = calcular_compatibles_anteriores(ordenadas)
    mejor = calcular_tabla_optima(ordenadas, compatibles)
    return mejor[-1]


def reconstruir_jornadas(
    ordenadas: list[Jornada], compatibles: list[int], mejor: list[int]
) -> list[Jornada]:
    """Reconstruye un subconjunto de jornadas con peso total óptimo.

    Ante un empate entre elegir y omitir una jornada, conserva la solución
    que ya estaba calculada sin esa jornada. Esta regla hace determinista la
    reconstrucción sin cambiar el valor óptimo.

    Args:
        ordenadas: Jornadas ordenadas de menor a mayor hora de finalización.
        compatibles: Lista ``p`` calculada para las mismas jornadas.
        mejor: Tabla ``M`` con el valor óptimo de cada prefijo.

    Returns:
        Las jornadas de una solución óptima, ordenadas por hora de inicio.

    Raises:
        ValueError: Si las tablas no corresponden al número de jornadas.
    """
    cantidad = len(ordenadas)
    if len(compatibles) != cantidad + 1 or len(mejor) != cantidad + 1:
        raise ValueError("Las tablas no corresponden a las jornadas ordenadas")

    elegidas: list[Jornada] = []
    j = cantidad
    while j > 0:
        pacientes = ordenadas[j - 1][2]
        valor_al_elegir = pacientes + mejor[compatibles[j]]
        if valor_al_elegir > mejor[j - 1]:
            elegidas.append(ordenadas[j - 1])
            j = compatibles[j]
        else:
            j -= 1

    elegidas.reverse()
    elegidas.sort(key=lambda jornada: (jornada[0], jornada[1], jornada[2]))
    return elegidas


def seleccionar_jornadas(solicitudes: list[Jornada]) -> list[Jornada]:
    """Elige las jornadas que maximizan los pacientes de alto riesgo.

    Dos jornadas que se tocan en un extremo se consideran compatibles. La
    función no modifica la lista recibida.

    Args:
        solicitudes: Solicitudes del mes de una subregión.

    Returns:
        Las jornadas elegidas sin cruces, ordenadas por hora de inicio.
    """
    ordenadas = ordenar_por_fin(solicitudes)
    compatibles = calcular_compatibles_anteriores(ordenadas)
    mejor = calcular_tabla_optima(ordenadas, compatibles)
    return reconstruir_jornadas(ordenadas, compatibles, mejor)
