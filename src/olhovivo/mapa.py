"""Street map: which rule applies to which area of the camera frame."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from olhovivo.modelos import Deteccao, ErroEntrada, Regra, Trecho


class Mapa:
    """Ordered set of stretches. When areas overlap, the first one listed wins."""

    def __init__(self, trechos: Iterable[Trecho]) -> None:
        self.trechos: tuple[Trecho, ...] = tuple(trechos)
        self._por_id: dict[str, Trecho] = {}
        for trecho in self.trechos:
            if trecho.id in self._por_id:
                raise ErroEntrada(f"id de trecho duplicado: {trecho.id!r}")
            self._por_id[trecho.id] = trecho

    def trecho(self, trecho_id: str) -> Trecho:
        return self._por_id[trecho_id]

    def trecho_de(self, deteccao: Deteccao) -> Trecho | None:
        """Stretch whose area contains the centre of the detection box, if any."""
        centro = deteccao.centro
        for trecho in self.trechos:
            if trecho.contem(centro):
                return trecho
        return None


def _trecho_de_dict(dados: Any, indice: int) -> Trecho:
    rotulo = f"trecho #{indice}"
    if not isinstance(dados, dict):
        raise ErroEntrada(f"{rotulo}: esperado um mapeamento")
    for campo in ("id", "regra", "area"):
        if campo not in dados:
            raise ErroEntrada(f"{rotulo}: campo obrigatorio ausente: {campo}")

    trecho_id = str(dados["id"])
    rotulo = f"trecho {trecho_id!r}"

    try:
        regra = Regra(dados["regra"])
    except ValueError as erro:
        validas = ", ".join(r.value for r in Regra)
        raise ErroEntrada(
            f"{rotulo}: regra desconhecida {dados['regra']!r} (validas: {validas})"
        ) from erro

    area = dados["area"]
    if (
        not isinstance(area, list)
        or len(area) != 4
        or any(isinstance(v, bool) or not isinstance(v, int | float) for v in area)
    ):
        raise ErroEntrada(f"{rotulo}: area deve ser uma lista de 4 numeros [x1, y1, x2, y2]")

    janela = dados.get("janela_minutos")
    if janela is not None and (isinstance(janela, bool) or not isinstance(janela, int)):
        raise ErroEntrada(f"{rotulo}: janela_minutos deve ser um inteiro")

    return Trecho(
        id=trecho_id,
        nome=str(dados.get("nome", trecho_id)),
        regra=regra,
        area=(float(area[0]), float(area[1]), float(area[2]), float(area[3])),
        janela_minutos=janela,
    )


def mapa_de_dict(dados: Any) -> Mapa:
    if not isinstance(dados, dict) or not isinstance(dados.get("trechos"), list):
        raise ErroEntrada("mapa: esperada a chave 'trechos' com uma lista")
    if not dados["trechos"]:
        raise ErroEntrada("mapa: a lista 'trechos' esta vazia")
    return Mapa(_trecho_de_dict(item, i) for i, item in enumerate(dados["trechos"]))


def carregar_mapa(caminho: str | Path) -> Mapa:
    try:
        dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    except yaml.YAMLError as erro:
        raise ErroEntrada(f"{caminho}: YAML invalido: {erro}") from erro
    try:
        return mapa_de_dict(dados)
    except ErroEntrada as erro:
        raise ErroEntrada(f"{caminho}: {erro}") from erro
