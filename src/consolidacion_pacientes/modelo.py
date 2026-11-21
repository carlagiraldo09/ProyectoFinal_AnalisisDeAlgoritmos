"""Modelo de datos compartido por las estrategias de consolidación."""

from dataclasses import dataclass
from datetime import datetime


ClavePaciente = tuple[str, str]


@dataclass(frozen=True)
class Resultado:
    """Resultado inmutable recibido de un laboratorio o una IPS."""

    tipo_documento: str
    numero_documento: str
    id_laboratorio: str
    id_lote: str
    fecha_resultado: datetime
    indice_riesgo: int
    municipio: str

    def __post_init__(self) -> None:
        """Valida los límites definidos para el índice de riesgo."""
        if not 0 <= self.indice_riesgo <= 100:
            raise ValueError("El índice de riesgo debe estar entre 0 y 100")

    @property
    def clave_paciente(self) -> ClavePaciente:
        """Retorna la identidad compuesta del paciente."""
        return self.tipo_documento, self.numero_documento
