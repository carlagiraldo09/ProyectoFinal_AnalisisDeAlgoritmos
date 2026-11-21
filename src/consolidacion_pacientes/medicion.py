"""Medición reproducible de tiempo, comparaciones y memoria."""

import csv
import tracemalloc
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import Any, TypeVar

from datos import generar_resultados
from modelo import ClavePaciente, Resultado
from ordenamiento import consolidar_ordenamiento
from secuencial import consolidar_secuencial
from tabla_hash import consolidar_hash


T = TypeVar("T")
Estrategia = Callable[[Sequence[Resultado]], list[Resultado]]
RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]
RUTA_RESULTADOS = RAIZ_REPOSITORIO / "resultados" / "consolidacion.csv"
REPETICIONES = 5
PROPORCION_DUPLICADOS = 0.12

ESTRATEGIAS: dict[str, Estrategia] = {
    "secuencial": consolidar_secuencial,
    "ordenamiento": consolidar_ordenamiento,
    "hash": consolidar_hash,
}


@dataclass(frozen=True)
class Medicion:
    """Resultado experimental para una estrategia y un tamaño."""

    cantidad: int
    estrategia: str
    tiempo_ms: float
    comparaciones: int
    memoria_pico_kib: float
    repeticiones: int


def medir_experimento(
    tamanos_comunes: Sequence[int] = (100, 250, 500, 1_000, 2_000, 4_000),
    tamanos_eficientes: Sequence[int] = (10_000, 25_000, 50_000, 100_000),
) -> list[Medicion]:
    """Mide las tres estrategias y amplía las eficientes a tamaños mayores."""
    mediciones: list[Medicion] = []

    for cantidad in tamanos_comunes:
        datos = generar_resultados(
            cantidad,
            PROPORCION_DUPLICADOS,
            semilla=2026 + cantidad,
        )
        for nombre in ESTRATEGIAS:
            mediciones.append(_medir(nombre, datos))

    for cantidad in tamanos_eficientes:
        datos = generar_resultados(
            cantidad,
            PROPORCION_DUPLICADOS,
            semilla=2026 + cantidad,
        )
        for nombre in ("ordenamiento", "hash"):
            mediciones.append(_medir(nombre, datos))

    return mediciones


def guardar_mediciones(
    mediciones: Sequence[Medicion],
    ruta: Path = RUTA_RESULTADOS,
) -> None:
    """Guarda las mediciones en CSV para analizarlas y graficarlas."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        campos = (
            "cantidad",
            "estrategia",
            "tiempo_ms",
            "comparaciones",
            "memoria_pico_kib",
            "repeticiones",
            "proporcion_duplicados",
        )
        escritor = csv.DictWriter(
            archivo,
            fieldnames=campos,
            lineterminator="\n",
        )
        escritor.writeheader()
        for medicion in mediciones:
            escritor.writerow(
                {
                    "cantidad": medicion.cantidad,
                    "estrategia": medicion.estrategia,
                    "tiempo_ms": f"{medicion.tiempo_ms:.6f}",
                    "comparaciones": medicion.comparaciones,
                    "memoria_pico_kib": f"{medicion.memoria_pico_kib:.3f}",
                    "repeticiones": medicion.repeticiones,
                    "proporcion_duplicados": PROPORCION_DUPLICADOS,
                }
            )


def _medir(nombre: str, datos: Sequence[Resultado]) -> Medicion:
    """Mide una estrategia sin incluir la generación de la entrada."""
    estrategia = ESTRATEGIAS[nombre]
    estrategia(datos)

    tiempos = []
    for _ in range(REPETICIONES):
        inicio = perf_counter()
        estrategia(datos)
        tiempos.append(perf_counter() - inicio)

    tracemalloc.start()
    estrategia(datos)
    _, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return Medicion(
        cantidad=len(datos),
        estrategia=nombre,
        tiempo_ms=mean(tiempos) * 1_000,
        comparaciones=CONTADORES[nombre](datos),
        memoria_pico_kib=memoria_pico / 1024,
        repeticiones=REPETICIONES,
    )


def contar_secuencial(resultados: Sequence[Resultado]) -> int:
    """Cuenta comparaciones de clave y fecha en la búsqueda secuencial."""
    consolidados: list[Resultado] = []
    comparaciones = 0

    for resultado in resultados:
        for posicion, guardado in enumerate(consolidados):
            comparaciones += 1
            if guardado.clave_paciente != resultado.clave_paciente:
                continue
            comparaciones += 1
            if resultado.fecha_resultado > guardado.fecha_resultado:
                consolidados[posicion] = resultado
            break
        else:
            consolidados.append(resultado)
    return comparaciones


def contar_ordenamiento(resultados: Sequence[Resultado]) -> int:
    """Cuenta comparaciones realizadas por la estrategia de merge sort."""
    numerados = list(enumerate(resultados))
    agrupados, comparaciones = _merge_contando(
        numerados,
        lambda elemento: elemento[1].clave_paciente,
    )
    seleccionados: list[tuple[int, Resultado]] = []
    posicion = 0

    while posicion < len(agrupados):
        primera_posicion, elegido = agrupados[posicion]
        clave = elegido.clave_paciente
        posicion += 1
        while posicion < len(agrupados):
            comparaciones += 1
            if agrupados[posicion][1].clave_paciente != clave:
                break
            candidato = agrupados[posicion][1]
            comparaciones += 1
            if candidato.fecha_resultado > elegido.fecha_resultado:
                elegido = candidato
            posicion += 1
        seleccionados.append((primera_posicion, elegido))

    _, comparaciones_finales = _merge_contando(
        seleccionados,
        lambda elemento: elemento[0],
    )
    return comparaciones + comparaciones_finales


def contar_hash(resultados: Sequence[Resultado]) -> int:
    """Cuenta comparaciones de la tabla con la misma dispersión implementada."""
    capacidad = 17
    cubetas: list[list[tuple[ClavePaciente, Resultado]]] = [
        [] for _ in range(capacidad)
    ]
    orden: list[ClavePaciente] = []
    cantidad = 0
    comparaciones = 0

    for resultado in resultados:
        clave = resultado.clave_paciente
        indice = _indice_hash(clave, capacidad)
        encontrado = False
        for posicion, (clave_guardada, guardado) in enumerate(cubetas[indice]):
            comparaciones += 1
            if clave_guardada != clave:
                continue
            comparaciones += 1
            if resultado.fecha_resultado > guardado.fecha_resultado:
                cubetas[indice][posicion] = clave, resultado
            encontrado = True
            break

        if encontrado:
            continue
        if (cantidad + 1) / capacidad > 0.75:
            capacidad, cubetas = _redimensionar_conteo(capacidad, cubetas)
            indice = _indice_hash(clave, capacidad)
        cubetas[indice].append((clave, resultado))
        orden.append(clave)
        cantidad += 1

    for clave in orden:
        indice = _indice_hash(clave, capacidad)
        for clave_guardada, _ in cubetas[indice]:
            comparaciones += 1
            if clave_guardada == clave:
                break
    return comparaciones


def _merge_contando(
    elementos: Sequence[T],
    clave: Callable[[T], Any],
) -> tuple[list[T], int]:
    """Ordena mediante merge sort y retorna sus comparaciones."""
    if len(elementos) <= 1:
        return list(elementos), 0
    mitad = len(elementos) // 2
    izquierda, comparaciones_izquierda = _merge_contando(
        elementos[:mitad], clave
    )
    derecha, comparaciones_derecha = _merge_contando(elementos[mitad:], clave)
    mezcla: list[T] = []
    indice_izquierdo = 0
    indice_derecho = 0
    comparaciones = comparaciones_izquierda + comparaciones_derecha

    while indice_izquierdo < len(izquierda) and indice_derecho < len(derecha):
        comparaciones += 1
        if clave(izquierda[indice_izquierdo]) <= clave(derecha[indice_derecho]):
            mezcla.append(izquierda[indice_izquierdo])
            indice_izquierdo += 1
        else:
            mezcla.append(derecha[indice_derecho])
            indice_derecho += 1
    mezcla.extend(izquierda[indice_izquierdo:])
    mezcla.extend(derecha[indice_derecho:])
    return mezcla, comparaciones


def _redimensionar_conteo(
    capacidad: int,
    cubetas: Sequence[Sequence[tuple[ClavePaciente, Resultado]]],
) -> tuple[int, list[list[tuple[ClavePaciente, Resultado]]]]:
    """Reubica las entradas como la implementación de la tabla hash."""
    nueva_capacidad = _siguiente_primo(capacidad * 2)
    nuevas_cubetas: list[list[tuple[ClavePaciente, Resultado]]] = [
        [] for _ in range(nueva_capacidad)
    ]
    for cubeta in cubetas:
        for clave, resultado in cubeta:
            indice = _indice_hash(clave, nueva_capacidad)
            nuevas_cubetas[indice].append((clave, resultado))
    return nueva_capacidad, nuevas_cubetas


def _indice_hash(clave: ClavePaciente, capacidad: int) -> int:
    """Replica la función FNV-1a de la tabla hash."""
    valor = 2_166_136_261
    for componente in clave:
        for caracter in componente:
            valor ^= ord(caracter)
            valor = (valor * 16_777_619) & 0xFFFFFFFF
        valor ^= 255
        valor = (valor * 16_777_619) & 0xFFFFFFFF
    return valor % capacidad


def _siguiente_primo(numero: int) -> int:
    """Retorna el primer primo mayor o igual que un número."""
    candidato = max(2, numero)
    while not _es_primo(candidato):
        candidato += 1
    return candidato


def _es_primo(numero: int) -> bool:
    """Indica si un número es primo."""
    divisor = 2
    while divisor * divisor <= numero:
        if numero % divisor == 0:
            return False
        divisor += 1
    return numero >= 2


CONTADORES: dict[str, Callable[[Sequence[Resultado]], int]] = {
    "secuencial": contar_secuencial,
    "ordenamiento": contar_ordenamiento,
    "hash": contar_hash,
}


if __name__ == "__main__":
    resultados = medir_experimento()
    guardar_mediciones(resultados)
    print(f"Mediciones guardadas en {RUTA_RESULTADOS}")
