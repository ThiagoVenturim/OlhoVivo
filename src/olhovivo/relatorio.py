"""Build the alert report a human traffic agent reviews.

The report never states that a fine was issued. Every alert carries a status
saying it is pending human review, and the report opens with that notice.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

from olhovivo.modelos import Infracao

AVISO = (
    "Apoio a decisao: estes alertas NAO sao autuacoes. Cada item exige revisao e "
    "confirmacao de um agente de transito habilitado antes de qualquer providencia."
)
STATUS_PENDENTE = "pendente_revisao_humana"
CAMPOS_ALERTA = (
    "track_id",
    "placa",
    "trecho",
    "trecho_nome",
    "regra",
    "inicio",
    "fim",
    "duracao_min",
    "evidencia",
    "status",
)


def mascarar_placa(placa: str | None) -> str | None:
    """Keep the first three characters and hide the rest, for logs and shared output."""
    if placa is None:
        return None
    return placa[:3] + "*" * max(len(placa) - 3, 0)


def montar_alerta(infracao: Infracao, mascarar_placas: bool = False) -> dict[str, Any]:
    placa = mascarar_placa(infracao.placa) if mascarar_placas else infracao.placa
    return {
        "track_id": infracao.track_id,
        "placa": placa,
        "trecho": infracao.trecho,
        "trecho_nome": infracao.trecho_nome,
        "regra": infracao.regra.value,
        "inicio": infracao.inicio.isoformat(),
        "fim": infracao.fim.isoformat(),
        "duracao_min": infracao.duracao_min,
        "evidencia": infracao.evidencia,
        "status": STATUS_PENDENTE,
    }


def montar_relatorio(
    infracoes: Iterable[Infracao], mascarar_placas: bool = False
) -> dict[str, Any]:
    alertas = [montar_alerta(i, mascarar_placas) for i in infracoes]
    return {"aviso": AVISO, "total_alertas": len(alertas), "alertas": alertas}


def formatar_json(relatorio: dict[str, Any]) -> str:
    return json.dumps(relatorio, ensure_ascii=False, indent=2)


def formatar_texto(relatorio: dict[str, Any]) -> str:
    linhas = [relatorio["aviso"], "", f"Alertas para revisao: {relatorio['total_alertas']}"]
    for numero, alerta in enumerate(relatorio["alertas"], start=1):
        linhas += [
            "",
            f"[{numero}] placa {alerta['placa'] or 'nao lida'} (track {alerta['track_id']})",
            f"    trecho:    {alerta['trecho_nome']} ({alerta['trecho']})",
            f"    regra:     {alerta['regra']}",
            f"    inicio:    {alerta['inicio']}",
            f"    fim:       {alerta['fim']}",
            f"    duracao:   {alerta['duracao_min']} min",
            f"    evidencia: {alerta['evidencia']}",
            f"    status:    {alerta['status']}",
        ]
    return "\n".join(linhas)
