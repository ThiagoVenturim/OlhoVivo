from datetime import timedelta

from conftest import CAIXAS, T0, estadia

from olhovivo.modelos import Deteccao
from olhovivo.tracking import medir_permanencias, resumir_veiculos


def em(trecho, minuto, track="t1", placa=None, pisca=None):
    return Deteccao(track, CAIXAS[trecho], T0 + timedelta(minutes=minuto), placa, pisca)


def test_mede_permanencia_entre_primeira_e_ultima_deteccao(mapa):
    (p,) = medir_permanencias([em("rot-2h", 0), em("rot-2h", 30), em("rot-2h", 75)], mapa)
    assert p.trecho_id == "rot-2h"
    assert p.inicio == T0
    assert p.duracao == timedelta(minutes=75)
    assert p.n_deteccoes == 3


def test_tracks_diferentes_nao_se_misturam(mapa):
    permanencias = medir_permanencias(
        estadia("rot-2h", 10, track="a") + estadia("rot-2h", 50, track="b"), mapa
    )
    assert {p.veiculo.track_id: p.duracao for p in permanencias} == {
        "a": timedelta(minutes=10),
        "b": timedelta(minutes=50),
    }


def test_mudar_de_trecho_encerra_a_permanencia(mapa):
    permanencias = medir_permanencias(
        [em("rot-2h", 0), em("rot-2h", 10), em("proibido", 11), em("proibido", 14)], mapa
    )
    assert [(p.trecho_id, p.duracao) for p in permanencias] == [
        ("rot-2h", timedelta(minutes=10)),
        ("proibido", timedelta(minutes=3)),
    ]


def test_sair_e_voltar_ao_trecho_nao_soma_o_tempo(mapa):
    permanencias = medir_permanencias(
        [em("rot-2h", 0), em("rot-2h", 100), em("fora", 101), em("rot-2h", 110), em("rot-2h", 200)],
        mapa,
    )
    assert [p.duracao for p in permanencias] == [timedelta(minutes=100), timedelta(minutes=90)]


def test_lacuna_maior_que_o_limite_divide_a_permanencia(mapa):
    deteccoes = [em("rot-2h", 0), em("rot-2h", 5), em("rot-2h", 100), em("rot-2h", 105)]
    assert len(medir_permanencias(deteccoes, mapa)) == 1
    divididas = medir_permanencias(deteccoes, mapa, lacuna_max=timedelta(minutes=30))
    assert [p.duracao for p in divididas] == [timedelta(minutes=5), timedelta(minutes=5)]


def test_deteccoes_fora_de_ordem_sao_ordenadas_por_timestamp(mapa):
    (p,) = medir_permanencias([em("rot-2h", 40), em("rot-2h", 0), em("rot-2h", 20)], mapa)
    assert p.duracao == timedelta(minutes=40)


def test_resumo_do_veiculo_usa_a_placa_mais_lida(mapa):
    deteccoes = [
        em("rot-2h", 0, placa="FAKE001"),
        em("rot-2h", 1, placa="FAKE0O1"),
        em("rot-2h", 2, placa="FAKE001"),
        em("rot-2h", 3, placa=None),
    ]
    veiculo = resumir_veiculos(deteccoes)["t1"]
    assert veiculo.placa == "FAKE001"
    assert veiculo.primeira_visao == T0
    assert veiculo.ultima_visao == T0 + timedelta(minutes=3)


def test_veiculo_sem_placa_lida_fica_com_placa_none(mapa):
    (p,) = medir_permanencias(estadia("rot-2h", 5, placa=None), mapa)
    assert p.veiculo.placa is None


def test_pisca_e_resumido_por_permanencia(mapa):
    permanencias = medir_permanencias(
        [
            em("pisca", 0, pisca=True),
            em("pisca", 2, pisca=False),
            em("proibido", 3, pisca=False),
            em("proibido", 5, pisca=None),
            em("rot-2h", 6),
        ],
        mapa,
    )
    assert [p.tem_pisca for p in permanencias] == [True, False, None]
