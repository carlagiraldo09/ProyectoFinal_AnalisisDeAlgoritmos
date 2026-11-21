"""Pruebas reproducibles de las estrategias de consolidación."""

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from random import Random

from datos import generar_resultados
from modelo import ClavePaciente, Resultado
from ordenamiento import consolidar_ordenamiento
from secuencial import consolidar_secuencial
from tabla_hash import TablaHashPacientes, consolidar_hash


Estrategia = Callable[[Sequence[Resultado]], list[Resultado]]
ESTRATEGIAS: tuple[Estrategia, ...] = (
    consolidar_secuencial,
    consolidar_ordenamiento,
    consolidar_hash,
)


def crear_resultado(
    tipo: str,
    numero: str,
    fecha: datetime,
    riesgo: int = 50,
    lote: str = "LOTE-PRUEBA",
) -> Resultado:
    """Crea un registro pequeño para los casos controlados."""
    return Resultado(
        tipo_documento=tipo,
        numero_documento=numero,
        id_laboratorio="LAB-001",
        id_lote=lote,
        fecha_resultado=fecha,
        indice_riesgo=riesgo,
        municipio="Medellín",
    )


def consolidar_referencia(resultados: Sequence[Resultado]) -> list[Resultado]:
    """Calcula el resultado esperado con estructuras estándar de Python."""
    elegidos: dict[ClavePaciente, Resultado] = {}
    orden: list[ClavePaciente] = []

    for resultado in resultados:
        clave = resultado.clave_paciente
        if clave not in elegidos:
            elegidos[clave] = resultado
            orden.append(clave)
        elif resultado.fecha_resultado > elegidos[clave].fecha_resultado:
            elegidos[clave] = resultado

    return [elegidos[clave] for clave in orden]


def probar_casos_limite() -> None:
    """Verifica entradas vacías, unitarias y claves parecidas."""
    fecha = datetime(2026, 1, 10)
    unico = crear_resultado("CC", "1", fecha)
    misma_cifra_otro_tipo = crear_resultado("TI", "1", fecha)

    for estrategia in ESTRATEGIAS:
        assert estrategia([]) == []
        assert estrategia([unico]) == [unico]
        assert estrategia([unico, misma_cifra_otro_tipo]) == [
            unico,
            misma_cifra_otro_tipo,
        ]


def probar_fechas_empates_y_orden() -> None:
    """Verifica fecha máxima, empate y orden de primera aparición."""
    fecha = datetime(2026, 2, 1)
    a_inicial = crear_resultado("CC", "10", fecha, 20, "A-1")
    b = crear_resultado("CC", "20", fecha, 30, "B-1")
    a_antiguo = crear_resultado(
        "CC", "10", fecha - timedelta(days=1), 90, "A-0"
    )
    a_reciente = crear_resultado(
        "CC", "10", fecha + timedelta(days=1), 40, "A-2"
    )
    a_empate = crear_resultado(
        "CC", "10", fecha + timedelta(days=1), 99, "A-3"
    )
    entrada = [a_inicial, b, a_antiguo, a_reciente, a_empate]
    esperada = [a_reciente, b]

    for estrategia in ESTRATEGIAS:
        copia = entrada.copy()
        assert estrategia(entrada) == esperada
        assert entrada == copia


def probar_modelo_y_generador() -> None:
    """Verifica límites, reproducibilidad y proporción de repetidos."""
    datos = generar_resultados(100, proporcion_duplicados=0.12, semilla=81)
    claves = {resultado.clave_paciente for resultado in datos}

    assert datos == generar_resultados(100, 0.12, 81)
    assert len(datos) == 100
    assert len(claves) == 88
    assert generar_resultados(0) == []
    assert all(0 <= resultado.indice_riesgo <= 100 for resultado in datos)

    _esperar_error(lambda: generar_resultados(-1), ValueError)
    _esperar_error(lambda: generar_resultados(10, -0.1), ValueError)
    _esperar_error(lambda: generar_resultados(10, 1.0), ValueError)
    _esperar_error(
        lambda: crear_resultado("CC", "1", datetime(2026, 1, 1), 101),
        ValueError,
    )


def probar_colisiones_y_redimensionamiento() -> None:
    """Fuerza una colisión y comprueba el control del factor de carga."""
    tabla = TablaHashPacientes(capacidad_inicial=2, factor_carga_maximo=1.0)
    primero, segundo = _buscar_claves_en_colision(tabla)
    fecha = datetime(2026, 3, 1)
    resultado_1 = crear_resultado(*primero, fecha)
    resultado_2 = crear_resultado(*segundo, fecha)
    tabla.guardar(resultado_1)
    tabla.guardar(resultado_2)

    assert tabla.obtener(primero) == resultado_1
    assert tabla.obtener(segundo) == resultado_2

    tabla = TablaHashPacientes(capacidad_inicial=2, factor_carga_maximo=0.5)
    for resultado in generar_resultados(40, 0, 32):
        tabla.guardar(resultado)
    assert tabla.capacidad > 2
    assert tabla.factor_carga <= 0.5
    _esperar_error(lambda: tabla.obtener(("CC", "NO-EXISTE")), KeyError)


def probar_instancias_aleatorias(
    cantidad_casos: int = 100,
    semilla: int = 2026,
) -> None:
    """Compara las estrategias con un oráculo en casos reproducibles."""
    aleatorio = Random(semilla)
    for caso in range(cantidad_casos):
        cantidad = aleatorio.randrange(201)
        proporcion = aleatorio.uniform(0.08, 0.15)
        entrada = generar_resultados(cantidad, proporcion, semilla + caso)
        copia = entrada.copy()
        esperada = consolidar_referencia(entrada)

        for estrategia in ESTRATEGIAS:
            assert estrategia(entrada) == esperada, (caso, estrategia.__name__)
        assert entrada == copia


def _buscar_claves_en_colision(
    tabla: TablaHashPacientes,
) -> tuple[ClavePaciente, ClavePaciente]:
    """Encuentra dos claves distintas asignadas a la misma cubeta."""
    vistas: dict[int, ClavePaciente] = {}
    for numero in range(100):
        clave = "CC", str(numero)
        indice = tabla._indice(clave)
        if indice in vistas:
            return vistas[indice], clave
        vistas[indice] = clave
    raise AssertionError("No se encontró una colisión para la prueba")


def _esperar_error(funcion: Callable[[], object], error: type[Exception]) -> None:
    """Comprueba que una llamada produzca la excepción esperada."""
    try:
        funcion()
    except error:
        return
    raise AssertionError(f"Se esperaba la excepción {error.__name__}")


def ejecutar_pruebas() -> None:
    """Ejecuta todas las pruebas de la consolidación."""
    probar_casos_limite()
    probar_fechas_empates_y_orden()
    probar_modelo_y_generador()
    probar_colisiones_y_redimensionamiento()
    probar_instancias_aleatorias()
    print("Pruebas correctas: casos controlados y 100 instancias aleatorias")


if __name__ == "__main__":
    ejecutar_pruebas()
