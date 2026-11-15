import json

from conftest import estadia

from olhovivo.fonte import FonteFake
from olhovivo.pipeline import analisar
from olhovivo.relatorio import (
    AVISO,
    CAMPOS_ALERTA,
    STATUS_PENDENTE,
    formatar_json,
    formatar_texto,
    mascarar_placa,
    montar_relatorio,
)


def infracoes_de_exemplo(mapa):
    deteccoes = estadia("rot-2h", 150) + estadia("proibido", 10, track="t4", placa=None)
    return analisar(FonteFake(deteccoes), mapa)


def test_alerta_tem_todos_os_campos_com_os_valores_da_infracao(mapa):
    relatorio = montar_relatorio(infracoes_de_exemplo(mapa))
    assert relatorio["total_alertas"] == 2
    alerta = relatorio["alertas"][0]
    assert tuple(alerta) == CAMPOS_ALERTA
    assert alerta == {
        "track_id": "t1",
        "placa": "FAKE001",
        "trecho": "rot-2h",
        "trecho_nome": "Rotativo 2h",
        "regra": "rotativo",
        "inicio": "2026-01-05T08:00:00",
        "fim": "2026-01-05T10:30:00",
        "duracao_min": 150.0,
        "evidencia": alerta["evidencia"],
        "status": STATUS_PENDENTE,
    }
    assert alerta["evidencia"]


def test_relatorio_declara_que_nao_e_autuacao(mapa):
    relatorio = montar_relatorio(infracoes_de_exemplo(mapa))
    assert relatorio["aviso"] == AVISO
    assert "NAO sao autuacoes" in AVISO
    assert all(a["status"] == "pendente_revisao_humana" for a in relatorio["alertas"])


def test_relatorio_vazio_mantem_o_aviso():
    relatorio = montar_relatorio([])
    assert relatorio == {"aviso": AVISO, "total_alertas": 0, "alertas": []}
    assert AVISO in formatar_texto(relatorio)


def test_formato_json_e_valido_e_equivalente(mapa):
    relatorio = montar_relatorio(infracoes_de_exemplo(mapa))
    assert json.loads(formatar_json(relatorio)) == relatorio


def test_formato_texto_mostra_os_campos_para_o_agente(mapa):
    texto = formatar_texto(montar_relatorio(infracoes_de_exemplo(mapa)))
    assert texto.startswith(AVISO)
    for esperado in (
        "FAKE001",
        "Rotativo 2h",
        "rotativo",
        "2026-01-05T08:00:00",
        "2026-01-05T10:30:00",
        "150.0 min",
        STATUS_PENDENTE,
        "placa nao lida",
    ):
        assert esperado in texto


def test_mascarar_placas_oculta_o_final(mapa):
    relatorio = montar_relatorio(infracoes_de_exemplo(mapa), mascarar_placas=True)
    assert relatorio["alertas"][0]["placa"] == "FAK****"
    assert relatorio["alertas"][1]["placa"] is None
    assert mascarar_placa("AB") == "AB"
