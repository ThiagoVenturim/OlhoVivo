"""Pluggable detection source.

``FonteDeteccao`` is the only thing the core knows about where detections come
from. ``FonteFake`` replays a predefined list and is what tests and the offline
demo use. A real source (a vehicle detector plus plate reader running over
video) would implement the same protocol; none ships in this package.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from olhovivo.modelos import Deteccao, ErroEntrada


@runtime_checkable
class FonteDeteccao(Protocol):
    def proximas(self) -> list[Deteccao]:
        """Return the next batch of detections; an empty list means the source is exhausted."""
        ...


class FonteFake:
    """Deterministic source that replays a fixed list, optionally in batches."""

    def __init__(self, deteccoes: Iterable[Deteccao], tamanho_lote: int | None = None) -> None:
        if tamanho_lote is not None and tamanho_lote <= 0:
            raise ValueError("tamanho_lote deve ser positivo")
        self._deteccoes = list(deteccoes)
        self._tamanho_lote = tamanho_lote
        self._posicao = 0

    def proximas(self) -> list[Deteccao]:
        if self._tamanho_lote is None:
            fim = len(self._deteccoes)
        else:
            fim = self._posicao + self._tamanho_lote
        lote = self._deteccoes[self._posicao : fim]
        self._posicao += len(lote)
        return lote


def consumir(fonte: FonteDeteccao) -> list[Deteccao]:
    """Drain a source until it returns an empty batch."""
    todas: list[Deteccao] = []
    while lote := fonte.proximas():
        todas.extend(lote)
    return todas


def deteccao_de_dict(dados: Any, indice: int = 0) -> Deteccao:
    rotulo = f"deteccao #{indice}"
    if not isinstance(dados, dict):
        raise ErroEntrada(f"{rotulo}: esperado um objeto")
    for campo in ("id_track", "bbox", "timestamp"):
        if campo not in dados:
            raise ErroEntrada(f"{rotulo}: campo obrigatorio ausente: {campo}")

    id_track = dados["id_track"]
    if isinstance(id_track, bool) or not isinstance(id_track, str | int) or id_track == "":
        raise ErroEntrada(f"{rotulo}: id_track deve ser texto ou inteiro")

    bbox = dados["bbox"]
    if (
        not isinstance(bbox, list)
        or len(bbox) != 4
        or any(isinstance(v, bool) or not isinstance(v, int | float) for v in bbox)
    ):
        raise ErroEntrada(f"{rotulo}: bbox deve ser uma lista de 4 numeros")

    try:
        timestamp = datetime.fromisoformat(dados["timestamp"])
    except (TypeError, ValueError) as erro:
        raise ErroEntrada(f"{rotulo}: timestamp deve estar em ISO 8601") from erro

    placa = dados.get("placa")
    if placa is not None and not isinstance(placa, str):
        raise ErroEntrada(f"{rotulo}: placa deve ser texto ou null")

    tem_pisca = dados.get("tem_pisca")
    if tem_pisca is not None and not isinstance(tem_pisca, bool):
        raise ErroEntrada(f"{rotulo}: tem_pisca deve ser true, false ou null")

    return Deteccao(
        id_track=str(id_track),
        bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
        timestamp=timestamp,
        placa=placa or None,
        tem_pisca=tem_pisca,
    )


def carregar_deteccoes(caminho: str | Path) -> list[Deteccao]:
    """Read detections from a JSON file: a list, or an object with a ``deteccoes`` list."""
    try:
        bruto = json.loads(Path(caminho).read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroEntrada(f"{caminho}: JSON invalido: {erro}") from erro

    if isinstance(bruto, dict):
        bruto = bruto.get("deteccoes")
    if not isinstance(bruto, list):
        raise ErroEntrada(f"{caminho}: esperada uma lista de deteccoes")

    deteccoes = [deteccao_de_dict(item, i) for i, item in enumerate(bruto)]
    com_fuso = {d.timestamp.tzinfo is not None for d in deteccoes}
    if len(com_fuso) > 1:
        raise ErroEntrada(f"{caminho}: nao misture timestamps com e sem fuso horario")
    return deteccoes
