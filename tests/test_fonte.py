import json
from datetime import datetime

import pytest
from conftest import EXEMPLOS, estadia

from olhovivo.fonte import FonteDeteccao, FonteFake, carregar_deteccoes, consumir
from olhovivo.modelos import ErroEntrada

VALIDA = {"id_track": 7, "bbox": [0, 0, 10, 10], "timestamp": "2026-01-05T08:00:00"}


def escrever(tmp_path, dados):
    caminho = tmp_path / "deteccoes.json"
    texto = dados if isinstance(dados, str) else json.dumps(dados)
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def test_fonte_fake_satisfaz_o_protocolo():
    assert isinstance(FonteFake([]), FonteDeteccao)


def test_fonte_fake_devolve_tudo_e_depois_esgota():
    deteccoes = estadia("rot-2h", 10)
    fonte = FonteFake(deteccoes)
    assert fonte.proximas() == deteccoes
    assert fonte.proximas() == []


def test_fonte_fake_em_lotes_preserva_a_ordem():
    deteccoes = estadia("rot-2h", 10) + estadia("carga", 10, track="t2")
    fonte = FonteFake(deteccoes, tamanho_lote=3)
    assert [len(fonte.proximas()) for _ in range(3)] == [3, 1, 0]
    assert consumir(FonteFake(deteccoes, tamanho_lote=1)) == deteccoes


def test_carrega_deteccoes_de_lista_json(tmp_path):
    completa = {**VALIDA, "placa": "FAKE001", "tem_pisca": True}
    d1, d2 = carregar_deteccoes(escrever(tmp_path, [VALIDA, completa]))
    assert d1.id_track == "7"
    assert d1.bbox == (0.0, 0.0, 10.0, 10.0)
    assert d1.timestamp == datetime(2026, 1, 5, 8, 0, 0)
    assert d1.placa is None
    assert d1.tem_pisca is None
    assert d2.placa == "FAKE001"
    assert d2.tem_pisca is True


def test_carrega_deteccoes_de_objeto_com_chave_deteccoes(tmp_path):
    assert len(carregar_deteccoes(escrever(tmp_path, {"deteccoes": [VALIDA]}))) == 1


def test_arquivo_de_exemplo_so_tem_placas_sinteticas():
    deteccoes = carregar_deteccoes(EXEMPLOS / "deteccoes.json")
    assert deteccoes
    assert all(d.placa is None or d.placa.startswith("FAKE") for d in deteccoes)


@pytest.mark.parametrize(
    ("dados", "trecho_do_erro"),
    [
        ("{nao e json", "JSON invalido"),
        ({"outra": []}, "lista de deteccoes"),
        ([{"bbox": [0, 0, 1, 1], "timestamp": "2026-01-05T08:00:00"}], "id_track"),
        ([{**VALIDA, "bbox": [0, 0, 1]}], "bbox"),
        ([{**VALIDA, "bbox": [5, 0, 1, 1]}], "x1 < x2"),
        ([{**VALIDA, "timestamp": "ontem"}], "ISO 8601"),
        ([{**VALIDA, "tem_pisca": "sim"}], "tem_pisca"),
        ([{**VALIDA, "placa": 123}], "placa"),
        ([VALIDA, {**VALIDA, "timestamp": "2026-01-05T08:00:00+00:00"}], "fuso"),
    ],
)
def test_deteccoes_invalidas_geram_erro_claro(tmp_path, dados, trecho_do_erro):
    with pytest.raises(ErroEntrada, match=trecho_do_erro):
        carregar_deteccoes(escrever(tmp_path, dados))
