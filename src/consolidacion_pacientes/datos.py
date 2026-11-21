"""Generación reproducible de resultados sintéticos de Plataforma Pulso."""

from datetime import datetime, timedelta
from random import Random

from modelo import Resultado


TIPOS_DOCUMENTO = ("CC", "TI", "CE")
MUNICIPIOS = ("Apartadó", "Bello", "Envigado", "Medellín", "Rionegro")


def generar_resultados(
    cantidad: int,
    proporcion_duplicados: float = 0.12,
    semilla: int = 2026,
) -> list[Resultado]:
    """Genera resultados ficticios con pacientes repetidos.

    ``proporcion_duplicados`` representa la fracción de registros adicionales
    de pacientes que ya aparecen en la colección. El redondeo puede producir
    una diferencia pequeña en entradas de pocos elementos.
    """
    if cantidad < 0:
        raise ValueError("La cantidad no puede ser negativa")
    if not 0 <= proporcion_duplicados < 1:
        raise ValueError("La proporción de duplicados debe estar entre 0 y 1")
    if cantidad == 0:
        return []

    aleatorio = Random(semilla)
    cantidad_duplicados = min(
        round(cantidad * proporcion_duplicados),
        cantidad - 1,
    )
    cantidad_pacientes = cantidad - cantidad_duplicados
    fecha_base = datetime(2026, 1, 1)

    resultados = [
        _crear_resultado_inicial(indice, fecha_base, aleatorio)
        for indice in range(cantidad_pacientes)
    ]

    for indice in range(cantidad_duplicados):
        original = aleatorio.choice(resultados[:cantidad_pacientes])
        resultados.append(
            Resultado(
                tipo_documento=original.tipo_documento,
                numero_documento=original.numero_documento,
                id_laboratorio=f"LAB-{aleatorio.randrange(1, 291):03d}",
                id_lote=f"LOTE-D-{indice:07d}",
                fecha_resultado=original.fecha_resultado
                + timedelta(hours=aleatorio.randrange(-240, 241)),
                indice_riesgo=aleatorio.randrange(101),
                municipio=aleatorio.choice(MUNICIPIOS),
            )
        )

    aleatorio.shuffle(resultados)
    return resultados


def _crear_resultado_inicial(
    indice: int,
    fecha_base: datetime,
    aleatorio: Random,
) -> Resultado:
    """Crea el primer resultado sintético de un paciente."""
    return Resultado(
        tipo_documento=TIPOS_DOCUMENTO[indice % len(TIPOS_DOCUMENTO)],
        numero_documento=f"SINT-{indice:09d}",
        id_laboratorio=f"LAB-{aleatorio.randrange(1, 291):03d}",
        id_lote=f"LOTE-{indice:09d}",
        fecha_resultado=fecha_base
        + timedelta(minutes=aleatorio.randrange(365 * 24 * 60)),
        indice_riesgo=aleatorio.randrange(101),
        municipio=aleatorio.choice(MUNICIPIOS),
    )
