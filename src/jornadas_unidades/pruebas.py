"""Pruebas reproducibles para la programación de jornadas móviles."""

import random

from estrategia import Jornada, calcular_valor_optimo, seleccionar_jornadas
from exhaustivo import seleccionar_exhaustivo
from regla_actual import asignar_por_llegada, hay_cruce


def sumar_pacientes(jornadas: list[Jornada]) -> int:
    """Suma los pacientes de un conjunto de jornadas.

    Args:
        jornadas: Jornadas cuyo peso total se quiere conocer.

    Returns:
        La cantidad total de pacientes de alto riesgo.
    """
    return sum(jornada[2] for jornada in jornadas)


def probar_casos_limite() -> None:
    """Verifica entradas vacías, unitarias, compatibles y cruzadas."""
    assert seleccionar_jornadas([]) == []
    assert seleccionar_exhaustivo([]) == []
    assert asignar_por_llegada([]) == []

    unica = [(60, 120, 8)]
    assert seleccionar_jornadas(unica) == unica
    assert seleccionar_exhaustivo(unica) == unica
    assert asignar_por_llegada(unica) == unica

    compatibles = [(0, 60, 5), (60, 120, 7), (120, 180, 9)]
    assert seleccionar_jornadas(compatibles) == compatibles
    assert not hay_cruce(seleccionar_jornadas(compatibles))

    cruzadas = [(0, 180, 10), (30, 150, 25), (60, 120, 40)]
    elegidas = seleccionar_jornadas(cruzadas)
    assert elegidas == [(60, 120, 40)]
    assert not hay_cruce(elegidas)


def probar_ejemplo_manual() -> None:
    """Verifica el ejemplo de seis jornadas resuelto en el informe."""
    solicitudes = [
        (480, 600, 20),
        (540, 720, 55),
        (600, 660, 15),
        (660, 780, 25),
        (720, 900, 50),
        (840, 960, 30),
    ]
    esperadas = [(540, 720, 55), (720, 900, 50)]
    assert seleccionar_jornadas(solicitudes) == esperadas
    assert calcular_valor_optimo(solicitudes) == 105
    assert sumar_pacientes(seleccionar_exhaustivo(solicitudes)) == 105


def probar_contraejemplo_regla_actual() -> None:
    """Verifica la instancia donde el orden de llegada no es óptimo."""
    solicitudes = [
        (480, 960, 30),
        (480, 720, 40),
        (720, 960, 45),
    ]
    actual = asignar_por_llegada(solicitudes)
    optima = seleccionar_jornadas(solicitudes)
    assert sumar_pacientes(actual) == 30
    assert sumar_pacientes(optima) == 85
    assert sumar_pacientes(optima) - sumar_pacientes(actual) == 55
    assert not hay_cruce(actual)
    assert not hay_cruce(optima)


def generar_instancia(azar: random.Random, cantidad: int) -> list[Jornada]:
    """Genera una instancia pequeña para comparar soluciones exactas.

    Args:
        azar: Generador inicializado con una semilla fija.
        cantidad: Número de solicitudes que se deben generar.

    Returns:
        Jornadas con horarios y cantidades de pacientes enteros.
    """
    solicitudes: list[Jornada] = []
    for _ in range(cantidad):
        inicio = azar.randrange(0, 24 * 60, 15)
        duracion = azar.randrange(30, 4 * 60 + 15, 15)
        pacientes = azar.randint(1, 100)
        solicitudes.append((inicio, inicio + duracion, pacientes))
    return solicitudes


def probar_instancias_aleatorias(
    cantidad_casos: int = 50, semilla: int = 2026
) -> None:
    """Compara la estrategia y la exhaustiva en casos aleatorios pequeños.

    Args:
        cantidad_casos: Número de instancias que se comparan.
        semilla: Semilla que permite reproducir exactamente las pruebas.
    """
    azar = random.Random(semilla)
    for _ in range(cantidad_casos):
        solicitudes = generar_instancia(azar, azar.randint(0, 10))
        copia = solicitudes.copy()
        dinamica = seleccionar_jornadas(solicitudes)
        exhaustiva = seleccionar_exhaustivo(solicitudes)

        assert sumar_pacientes(dinamica) == sumar_pacientes(exhaustiva), (
            solicitudes,
            dinamica,
            exhaustiva,
        )
        assert sumar_pacientes(dinamica) == calcular_valor_optimo(solicitudes)
        assert not hay_cruce(dinamica)
        assert solicitudes == copia


def ejecutar_pruebas() -> None:
    """Ejecuta todas las pruebas del laboratorio."""
    probar_casos_limite()
    probar_ejemplo_manual()
    probar_contraejemplo_regla_actual()
    probar_instancias_aleatorias()
    print("Pruebas correctas: casos límite y 50 instancias aleatorias")


if __name__ == "__main__":
    ejecutar_pruebas()
