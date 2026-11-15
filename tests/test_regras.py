from datetime import timedelta

import pytest
from conftest import T0, estadia

from olhovivo.fonte import FonteFake
from olhovivo.modelos import Deteccao, Regra
from olhovivo.pipeline import analisar
from olhovivo.regras import avaliar
from olhovivo.tracking import medir_permanencias


def rodar(deteccoes, mapa, **kwargs):
    return analisar(FonteFake(deteccoes), mapa, **kwargs)


# rotativo


def test_rotativo_acima_da_janela_gera_infracao(mapa):
    (infracao,) = rodar(estadia("rot-2h", 150), mapa)
    assert infracao.regra is Regra.ROTATIVO
    assert infracao.trecho == "rot-2h"
    assert infracao.placa == "FAKE001"
    assert infracao.duracao_min == 150.0
    assert infracao.inicio == T0
    assert infracao.fim == T0 + timedelta(minutes=150)
    assert "120 min" in infracao.evidencia


def test_rotativo_dentro_da_janela_nao_gera_infracao(mapa):
    assert rodar(estadia("rot-2h", 90), mapa) == []


def test_rotativo_exatamente_na_janela_nao_gera_infracao(mapa):
    assert rodar(estadia("rot-2h", 120), mapa) == []


def test_rotativo_um_segundo_acima_da_janela_gera_infracao(mapa):
    assert len(rodar(estadia("rot-2h", 120 + 1 / 60), mapa)) == 1


# carga e descarga


def test_carga_descarga_acima_da_janela_gera_infracao(mapa):
    (infracao,) = rodar(estadia("carga", 45), mapa)
    assert infracao.regra is Regra.CARGA_DESCARGA
    assert infracao.duracao_min == 45.0


def test_carga_descarga_dentro_da_janela_nao_gera_infracao(mapa):
    assert rodar(estadia("carga", 20), mapa) == []


# proibido


def test_proibido_parado_gera_infracao(mapa):
    (infracao,) = rodar(estadia("proibido", 10), mapa)
    assert infracao.regra is Regra.PROIBIDO


def test_proibido_de_passagem_nao_gera_infracao(mapa):
    assert rodar(estadia("proibido", 20 / 60), mapa) == []


def test_proibido_respeita_limiar_de_parado_configurado(mapa):
    deteccoes = estadia("proibido", 2)
    assert len(rodar(deteccoes, mapa, parado_min=timedelta(minutes=1))) == 1
    assert rodar(deteccoes, mapa, parado_min=timedelta(minutes=5)) == []


def test_proibido_com_uma_unica_deteccao_nao_gera_infracao(mapa):
    assert rodar(estadia("proibido", 10)[:1], mapa) == []


# so_pisca


def test_so_pisca_parado_sem_pisca_gera_infracao(mapa):
    (infracao,) = rodar(estadia("pisca", 5, pisca=False), mapa)
    assert infracao.regra is Regra.SO_PISCA
    assert "sem pisca-alerta" in infracao.evidencia


def test_so_pisca_com_pisca_ligado_nao_gera_infracao(mapa):
    assert rodar(estadia("pisca", 5, pisca=True), mapa) == []


def test_so_pisca_visto_ligado_uma_vez_conta_como_ligado(mapa):
    deteccoes = estadia("pisca", 5, pisca=False)
    deteccoes.append(Deteccao("t1", deteccoes[0].bbox, T0 + timedelta(minutes=2), None, True))
    assert rodar(deteccoes, mapa) == []


def test_so_pisca_sem_informacao_de_pisca_nao_gera_infracao(mapa):
    assert rodar(estadia("pisca", 5, pisca=None), mapa) == []


def test_so_pisca_de_passagem_sem_pisca_nao_gera_infracao(mapa):
    assert rodar(estadia("pisca", 0.5, pisca=False), mapa) == []


def test_so_pisca_com_janela_excedida_gera_infracao_mesmo_com_pisca(mapa):
    (infracao,) = rodar(estadia("pisca-30", 40, pisca=True), mapa)
    assert "30 min" in infracao.evidencia
    assert rodar(estadia("pisca-30", 20, pisca=True), mapa) == []


# general behaviour


def test_veiculo_fora_de_qualquer_trecho_nao_gera_infracao(mapa):
    assert rodar(estadia("fora", 600), mapa) == []


def test_varios_veiculos_saem_ordenados_e_so_os_irregulares(mapa):
    deteccoes = (
        estadia("carga", 45, track="t8", placa="FAKE008", inicio=T0 + timedelta(hours=1))
        + estadia("rot-2h", 150, track="t1", placa="FAKE001")
        + estadia("rot-2h", 60, track="t2", placa="FAKE002")
    )
    infracoes = rodar(deteccoes, mapa)
    assert [i.track_id for i in infracoes] == ["t1", "t8"]


def test_resultado_e_deterministico_e_independe_da_ordem_de_entrada(mapa):
    deteccoes = estadia("rot-2h", 150) + estadia("proibido", 10, track="t4", placa="FAKE004")
    assert rodar(deteccoes, mapa) == rodar(list(reversed(deteccoes)), mapa)
    assert rodar(deteccoes, mapa) == rodar(deteccoes, mapa)


def test_avaliar_recusa_trecho_que_nao_e_o_da_permanencia(mapa):
    (permanencia,) = medir_permanencias(estadia("rot-2h", 150), mapa)
    with pytest.raises(ValueError):
        avaliar(permanencia, mapa.trecho("carga"))
