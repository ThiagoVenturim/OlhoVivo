import pytest
from conftest import EXEMPLOS, T0

from olhovivo.mapa import Mapa, carregar_mapa
from olhovivo.modelos import Deteccao, ErroEntrada, Regra, Trecho

YAML_VALIDO = """
trechos:
  - id: a
    nome: Trecho A
    regra: rotativo
    janela_minutos: 120
    area: [0, 0, 100, 100]
  - id: b
    regra: proibido
    area: [100, 0, 200, 100]
"""


def escrever(tmp_path, texto):
    caminho = tmp_path / "mapa.yaml"
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def det(bbox):
    return Deteccao("t1", bbox, T0)


def test_carrega_trechos_do_yaml(tmp_path):
    mapa = carregar_mapa(escrever(tmp_path, YAML_VALIDO))
    assert [t.id for t in mapa.trechos] == ["a", "b"]
    a = mapa.trecho("a")
    assert a.nome == "Trecho A"
    assert a.regra is Regra.ROTATIVO
    assert a.janela_minutos == 120
    assert a.area == (0.0, 0.0, 100.0, 100.0)
    b = mapa.trecho("b")
    assert b.nome == "b"
    assert b.regra is Regra.PROIBIDO
    assert b.janela_minutos is None


def test_associa_deteccao_ao_trecho_pelo_centro_da_caixa(tmp_path):
    mapa = carregar_mapa(escrever(tmp_path, YAML_VALIDO))
    assert mapa.trecho_de(det((10, 10, 50, 50))).id == "a"
    assert mapa.trecho_de(det((120, 10, 180, 50))).id == "b"
    # Box overlaps both areas, but its centre (105, 30) is in b.
    assert mapa.trecho_de(det((60, 10, 150, 50))).id == "b"


def test_deteccao_fora_de_todas_as_areas_nao_tem_trecho(tmp_path):
    mapa = carregar_mapa(escrever(tmp_path, YAML_VALIDO))
    assert mapa.trecho_de(det((500, 500, 600, 600))) is None


def test_em_areas_sobrepostas_vence_o_primeiro_trecho():
    mapa = Mapa(
        [
            Trecho("primeiro", "Primeiro", Regra.PROIBIDO, (0, 0, 100, 100)),
            Trecho("segundo", "Segundo", Regra.PROIBIDO, (50, 0, 150, 100)),
        ]
    )
    assert mapa.trecho_de(det((60, 10, 90, 50))).id == "primeiro"


def test_mapa_de_exemplo_carrega_as_quatro_regras():
    mapa = carregar_mapa(EXEMPLOS / "mapa.yaml")
    assert {t.regra for t in mapa.trechos} == set(Regra)


@pytest.mark.parametrize(
    ("texto", "trecho_do_erro"),
    [
        ("trechos: []", "vazia"),
        ("outra_chave: 1", "trechos"),
        ("trechos:\n  - id: a\n    regra: rotativo\n    area: [0, 0, 1, 1]", "janela_minutos"),
        ("trechos:\n  - id: a\n    regra: carga_descarga\n    area: [0, 0, 1, 1]", "janela_minutos"),
        ("trechos:\n  - id: a\n    regra: zona_azul\n    area: [0, 0, 1, 1]", "regra desconhecida"),
        ("trechos:\n  - id: a\n    regra: proibido\n    area: [0, 0, 1]", "area"),
        ("trechos:\n  - id: a\n    regra: proibido\n    area: [5, 0, 1, 1]", "x1 < x2"),
        ("trechos:\n  - id: a\n    regra: proibido", "area"),
        (
            "trechos:\n  - id: a\n    regra: rotativo\n    janela_minutos: 0\n    area: [0, 0, 1, 1]",
            "positivo",
        ),
        (
            "trechos:\n"
            "  - id: a\n    regra: proibido\n    area: [0, 0, 1, 1]\n"
            "  - id: a\n    regra: proibido\n    area: [1, 0, 2, 1]",
            "duplicado",
        ),
        ("trechos: [", "YAML invalido"),
    ],
)
def test_mapa_invalido_gera_erro_claro(tmp_path, texto, trecho_do_erro):
    with pytest.raises(ErroEntrada, match=trecho_do_erro):
        carregar_mapa(escrever(tmp_path, texto))
