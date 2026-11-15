"""Decision logic: does a stay in a stretch break that stretch's rule?

Pure functions over ``Permanencia`` and ``Trecho``. No clock, no randomness,
no I/O: the same input always gives the same output.

Summary of the rules:

- rotativo / carga_descarga: infraction when the stay is longer than ``janela_minutos``.
- proibido: infraction when the vehicle is stopped (stay of at least ``parado_min``).
- so_pisca: infraction when stopped with hazard lights seen off. If the source
  never reported the hazard lights, no alert is raised, because there is no
  evidence either way. If the stretch also has ``janela_minutos``, staying
  longer than that is an infraction even with hazard lights on.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from olhovivo.mapa import Mapa
from olhovivo.modelos import Infracao, Regra, Trecho
from olhovivo.tracking import Permanencia

# A vehicle seen in a stretch for less than this is treated as passing through.
PARADO_MIN_PADRAO = timedelta(seconds=60)


def _minutos(duracao: timedelta) -> float:
    return round(duracao.total_seconds() / 60, 2)


def _motivo(permanencia: Permanencia, trecho: Trecho, parado_min: timedelta) -> str | None:
    duracao = permanencia.duracao
    minutos = _minutos(duracao)
    janela = trecho.janela_minutos
    excedeu_janela = janela is not None and duracao > timedelta(minutes=janela)
    parado = duracao >= parado_min

    match trecho.regra:
        case Regra.ROTATIVO:
            if excedeu_janela:
                return f"permanencia de {minutos} min excede a janela de {janela} min do rotativo"
        case Regra.CARGA_DESCARGA:
            if excedeu_janela:
                return (
                    f"permanencia de {minutos} min excede a janela de {janela} min "
                    "de carga e descarga"
                )
        case Regra.PROIBIDO:
            if parado:
                return f"veiculo parado por {minutos} min em trecho de estacionamento proibido"
        case Regra.SO_PISCA:
            if parado and permanencia.tem_pisca is False:
                return f"veiculo parado por {minutos} min sem pisca-alerta ligado"
            if parado and excedeu_janela:
                return (
                    f"permanencia de {minutos} min excede a janela de {janela} min "
                    "permitida com pisca-alerta"
                )
    return None


def avaliar(
    permanencia: Permanencia,
    trecho: Trecho,
    parado_min: timedelta = PARADO_MIN_PADRAO,
) -> Infracao | None:
    """Return the suspected infraction for one stay, or None when the stay is within the rule."""
    if permanencia.trecho_id != trecho.id:
        raise ValueError(
            f"permanencia do trecho {permanencia.trecho_id!r} avaliada contra {trecho.id!r}"
        )
    motivo = _motivo(permanencia, trecho, parado_min)
    if motivo is None:
        return None
    return Infracao(
        track_id=permanencia.veiculo.track_id,
        placa=permanencia.veiculo.placa,
        trecho=trecho.id,
        trecho_nome=trecho.nome,
        regra=trecho.regra,
        inicio=permanencia.inicio,
        fim=permanencia.fim,
        duracao_min=_minutos(permanencia.duracao),
        evidencia=f"{motivo} ({permanencia.n_deteccoes} deteccoes)",
    )


def avaliar_todas(
    permanencias: Iterable[Permanencia],
    mapa: Mapa,
    parado_min: timedelta = PARADO_MIN_PADRAO,
) -> list[Infracao]:
    infracoes = []
    for permanencia in permanencias:
        infracao = avaliar(permanencia, mapa.trecho(permanencia.trecho_id), parado_min)
        if infracao is not None:
            infracoes.append(infracao)
    infracoes.sort(key=lambda i: (i.inicio, i.track_id, i.trecho))
    return infracoes
