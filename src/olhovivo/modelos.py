"""Data model shared by every module. Plain frozen dataclasses, no behaviour beyond validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

# Rectangle in frame pixels: (x1, y1, x2, y2) with x1 < x2 and y1 < y2.
Caixa = tuple[float, float, float, float]


class ErroEntrada(ValueError):
    """Invalid map, detection file or model value supplied by the user."""


class Regra(StrEnum):
    ROTATIVO = "rotativo"
    PROIBIDO = "proibido"
    CARGA_DESCARGA = "carga_descarga"
    SO_PISCA = "so_pisca"


# Rules that only make sense with a time window.
REGRAS_COM_JANELA = frozenset({Regra.ROTATIVO, Regra.CARGA_DESCARGA})


def _validar_caixa(caixa: Caixa, rotulo: str) -> None:
    if len(caixa) != 4:
        raise ErroEntrada(f"{rotulo}: esperados 4 numeros (x1, y1, x2, y2)")
    x1, y1, x2, y2 = caixa
    if not (x1 < x2 and y1 < y2):
        raise ErroEntrada(f"{rotulo}: exige x1 < x2 e y1 < y2, recebido {list(caixa)}")


@dataclass(frozen=True, slots=True)
class Deteccao:
    """One vehicle sighting in one frame, as produced by a detection source."""

    id_track: str
    bbox: Caixa
    timestamp: datetime
    placa: str | None = None
    # True/False when the source could tell whether hazard lights were on, None when unknown.
    tem_pisca: bool | None = None

    def __post_init__(self) -> None:
        _validar_caixa(self.bbox, f"deteccao {self.id_track!r}: bbox")

    @property
    def centro(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)


@dataclass(frozen=True, slots=True)
class Trecho:
    """A stretch of kerb with one parking rule, located by a rectangle in the frame."""

    id: str
    nome: str
    regra: Regra
    area: Caixa
    janela_minutos: int | None = None

    def __post_init__(self) -> None:
        _validar_caixa(self.area, f"trecho {self.id!r}: area")
        if self.janela_minutos is not None and self.janela_minutos <= 0:
            raise ErroEntrada(f"trecho {self.id!r}: janela_minutos deve ser positivo")
        if self.regra in REGRAS_COM_JANELA and self.janela_minutos is None:
            raise ErroEntrada(
                f"trecho {self.id!r}: a regra {self.regra.value} exige janela_minutos"
            )

    def contem(self, ponto: tuple[float, float]) -> bool:
        x, y = ponto
        x1, y1, x2, y2 = self.area
        return x1 <= x <= x2 and y1 <= y <= y2


@dataclass(frozen=True, slots=True)
class Veiculo:
    """Summary of one track over the whole analysed period."""

    track_id: str
    placa: str | None
    primeira_visao: datetime
    ultima_visao: datetime
    tem_pisca: bool | None


@dataclass(frozen=True, slots=True)
class Infracao:
    """A suspected rule violation. It is an alert for human review, not a fine."""

    track_id: str
    placa: str | None
    trecho: str
    trecho_nome: str
    regra: Regra
    inicio: datetime
    fim: datetime
    duracao_min: float
    evidencia: str
