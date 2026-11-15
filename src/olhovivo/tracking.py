"""Group detections by track and measure how long each vehicle stayed in each stretch.

There is no visual tracker here. The ``id_track`` on each detection is trusted
as the vehicle identity; producing stable ids from video is the job of the
detection source.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from olhovivo.mapa import Mapa
from olhovivo.modelos import Deteccao, Veiculo


@dataclass(frozen=True, slots=True)
class Permanencia:
    """One uninterrupted stay of a vehicle in a stretch."""

    veiculo: Veiculo
    trecho_id: str
    inicio: datetime
    fim: datetime
    # Hazard lights during this stay only; see ``_resumir_pisca``.
    tem_pisca: bool | None
    n_deteccoes: int

    @property
    def duracao(self) -> timedelta:
        return self.fim - self.inicio


def _resumir_pisca(deteccoes: Iterable[Deteccao]) -> bool | None:
    """True if seen on at least once, False if only ever seen off, None if never observed.

    Hazard lights blink, so a single frame showing them off proves little while
    a single frame showing them on is enough.
    """
    valores = {d.tem_pisca for d in deteccoes}
    if True in valores:
        return True
    if False in valores:
        return False
    return None


def _placa_mais_lida(deteccoes: Iterable[Deteccao]) -> str | None:
    contagem = Counter(d.placa for d in deteccoes if d.placa)
    if not contagem:
        return None
    # Most frequent reading; ties broken alphabetically so the result is stable.
    return min(contagem, key=lambda placa: (-contagem[placa], placa))


def _por_track(deteccoes: Iterable[Deteccao]) -> dict[str, list[Deteccao]]:
    grupos: dict[str, list[Deteccao]] = {}
    for deteccao in deteccoes:
        grupos.setdefault(deteccao.id_track, []).append(deteccao)
    for grupo in grupos.values():
        grupo.sort(key=lambda d: d.timestamp)
    return grupos


def _veiculo(track_id: str, deteccoes: list[Deteccao]) -> Veiculo:
    return Veiculo(
        track_id=track_id,
        placa=_placa_mais_lida(deteccoes),
        primeira_visao=deteccoes[0].timestamp,
        ultima_visao=deteccoes[-1].timestamp,
        tem_pisca=_resumir_pisca(deteccoes),
    )


def _permanencia(veiculo: Veiculo, trecho_id: str, deteccoes: list[Deteccao]) -> Permanencia:
    return Permanencia(
        veiculo=veiculo,
        trecho_id=trecho_id,
        inicio=deteccoes[0].timestamp,
        fim=deteccoes[-1].timestamp,
        tem_pisca=_resumir_pisca(deteccoes),
        n_deteccoes=len(deteccoes),
    )


def resumir_veiculos(deteccoes: Iterable[Deteccao]) -> dict[str, Veiculo]:
    return {tid: _veiculo(tid, grupo) for tid, grupo in _por_track(deteccoes).items()}


def medir_permanencias(
    deteccoes: Iterable[Deteccao],
    mapa: Mapa,
    lacuna_max: timedelta | None = None,
) -> list[Permanencia]:
    """Split each track into stays and return them ordered by start time.

    A stay ends when the vehicle is next seen in another stretch or outside
    every stretch, or when the gap since the previous detection exceeds
    ``lacuna_max`` (no gap limit when None).
    """
    permanencias: list[Permanencia] = []

    for track_id, grupo in _por_track(deteccoes).items():
        veiculo = _veiculo(track_id, grupo)
        trecho_atual: str | None = None
        atual: list[Deteccao] = []

        for deteccao in grupo:
            trecho = mapa.trecho_de(deteccao)
            trecho_id = trecho.id if trecho else None
            lacuna = (
                lacuna_max is not None
                and bool(atual)
                and deteccao.timestamp - atual[-1].timestamp > lacuna_max
            )
            if trecho_id != trecho_atual or lacuna:
                if trecho_atual is not None:
                    permanencias.append(_permanencia(veiculo, trecho_atual, atual))
                trecho_atual = trecho_id
                atual = []
            if trecho_id is not None:
                atual.append(deteccao)
        if trecho_atual is not None:
            permanencias.append(_permanencia(veiculo, trecho_atual, atual))

    permanencias.sort(key=lambda p: (p.inicio, p.veiculo.track_id, p.trecho_id))
    return permanencias
