"""Consolidación con una tabla hash propia y encadenamiento."""

from collections.abc import Sequence

from modelo import ClavePaciente, Resultado


Entrada = tuple[ClavePaciente, Resultado]


class TablaHashPacientes:
    """Asocia cada clave de paciente con su resultado más reciente."""

    def __init__(
        self,
        capacidad_inicial: int = 17,
        factor_carga_maximo: float = 0.75,
    ) -> None:
        if capacidad_inicial < 2:
            raise ValueError("La capacidad inicial debe ser al menos 2")
        if not 0 < factor_carga_maximo <= 1:
            raise ValueError("El factor de carga máximo debe estar entre 0 y 1")

        self._capacidad = _siguiente_primo(capacidad_inicial)
        self._factor_carga_maximo = factor_carga_maximo
        self._cubetas: list[list[Entrada]] = [
            [] for _ in range(self._capacidad)
        ]
        self._orden_claves: list[ClavePaciente] = []
        self._cantidad = 0

    @property
    def capacidad(self) -> int:
        """Retorna la cantidad actual de cubetas."""
        return self._capacidad

    @property
    def cantidad(self) -> int:
        """Retorna la cantidad de pacientes almacenados."""
        return self._cantidad

    @property
    def factor_carga(self) -> float:
        """Retorna la razón entre pacientes y cubetas."""
        return self._cantidad / self._capacidad

    def guardar(self, resultado: Resultado) -> None:
        """Inserta un paciente o actualiza únicamente con una fecha posterior."""
        clave = resultado.clave_paciente
        cubeta = self._cubetas[self._indice(clave)]

        for posicion, (clave_guardada, guardado) in enumerate(cubeta):
            if clave_guardada != clave:
                continue
            if resultado.fecha_resultado > guardado.fecha_resultado:
                cubeta[posicion] = clave, resultado
            return

        if (self._cantidad + 1) / self._capacidad > self._factor_carga_maximo:
            self._redimensionar()
            cubeta = self._cubetas[self._indice(clave)]

        cubeta.append((clave, resultado))
        self._orden_claves.append(clave)
        self._cantidad += 1

    def obtener(self, clave: ClavePaciente) -> Resultado:
        """Busca el resultado asociado con una clave completa."""
        for clave_guardada, resultado in self._cubetas[self._indice(clave)]:
            if clave_guardada == clave:
                return resultado
        raise KeyError(clave)

    def resultados_en_orden(self) -> list[Resultado]:
        """Retorna los resultados según la primera aparición del paciente."""
        return [self.obtener(clave) for clave in self._orden_claves]

    def _indice(self, clave: ClavePaciente) -> int:
        """Calcula un índice determinista mediante mezcla FNV-1a y división."""
        valor = 2_166_136_261
        for componente in clave:
            for caracter in componente:
                valor ^= ord(caracter)
                valor = (valor * 16_777_619) & 0xFFFFFFFF
            valor ^= 255
            valor = (valor * 16_777_619) & 0xFFFFFFFF
        return valor % self._capacidad

    def _redimensionar(self) -> None:
        """Duplica aproximadamente las cubetas y reubica las entradas."""
        entradas = [entrada for cubeta in self._cubetas for entrada in cubeta]
        self._capacidad = _siguiente_primo(self._capacidad * 2)
        self._cubetas = [[] for _ in range(self._capacidad)]

        for clave, resultado in entradas:
            self._cubetas[self._indice(clave)].append((clave, resultado))


def consolidar_hash(resultados: Sequence[Resultado]) -> list[Resultado]:
    """Conserva por tabla hash el resultado más reciente de cada paciente."""
    tabla = TablaHashPacientes()
    for resultado in resultados:
        tabla.guardar(resultado)
    return tabla.resultados_en_orden()


def _siguiente_primo(numero: int) -> int:
    """Retorna el primer número primo mayor o igual que ``numero``."""
    candidato = max(2, numero)
    while not _es_primo(candidato):
        candidato += 1
    return candidato


def _es_primo(numero: int) -> bool:
    """Indica si un entero es primo mediante división hasta su raíz."""
    if numero < 2:
        return False
    divisor = 2
    while divisor * divisor <= numero:
        if numero % divisor == 0:
            return False
        divisor += 1
    return True
