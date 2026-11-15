"""End-to-end run of the core: source -> stays -> rule decisions."""

from __future__ import annotations

from datetime import timedelta

from olhovivo.fonte import FonteDeteccao, consumir
from olhovivo.mapa import Mapa
from olhovivo.modelos import Infracao
from olhovivo.regras import PARADO_MIN_PADRAO, avaliar_todas
from olhovivo.tracking import medir_permanencias


def analisar(
    fonte: FonteDeteccao,
    mapa: Mapa,
    *,
    parado_min: timedelta = PARADO_MIN_PADRAO,
    lacuna_max: timedelta | None = None,
) -> list[Infracao]:
    """Drain the source and return the suspected infractions, ordered by start time."""
    deteccoes = consumir(fonte)
    permanencias = medir_permanencias(deteccoes, mapa, lacuna_max=lacuna_max)
    return avaliar_todas(permanencias, mapa, parado_min=parado_min)
