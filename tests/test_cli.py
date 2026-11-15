import json

import pytest
from conftest import EXEMPLOS

from olhovivo.cli import main

MAPA = str(EXEMPLOS / "mapa.yaml")
DETECCOES = str(EXEMPLOS / "deteccoes.json")


def test_demo_em_json_aponta_exatamente_os_veiculos_irregulares(capsys):
    assert main(["analisar", "--mapa", MAPA, "--deteccoes", DETECCOES, "--formato", "json"]) == 0
    relatorio = json.loads(capsys.readouterr().out)
    encontrados = {(a["placa"], a["regra"]) for a in relatorio["alertas"]}
    assert encontrados == {
        ("FAKE001", "rotativo"),
        ("FAKE004", "proibido"),
        ("FAKE006", "so_pisca"),
        ("FAKE008", "carga_descarga"),
    }
    assert relatorio["total_alertas"] == 4


def test_demo_em_texto_abre_com_o_aviso_de_apoio_a_decisao(capsys):
    assert main(["analisar", "--mapa", MAPA, "--deteccoes", DETECCOES]) == 0
    saida = capsys.readouterr().out
    assert saida.startswith("Apoio a decisao")
    assert "Alertas para revisao: 4" in saida


def test_mascarar_placas_na_saida(capsys):
    main(["analisar", "--mapa", MAPA, "--deteccoes", DETECCOES, "--mascarar-placas"])
    saida = capsys.readouterr().out
    assert "FAK****" in saida
    assert "FAKE001" not in saida


def test_limiar_de_parado_configuravel(capsys):
    args = ["analisar", "--mapa", MAPA, "--deteccoes", DETECCOES, "--formato", "json"]
    main([*args, "--parado-segundos", "10"])
    placas = {a["placa"] for a in json.loads(capsys.readouterr().out)["alertas"]}
    assert "FAKE005" in placas


def test_arquivo_inexistente_retorna_codigo_2(capsys, tmp_path):
    codigo = main(["analisar", "--mapa", str(tmp_path / "nao-existe.yaml"), "--deteccoes", DETECCOES])
    assert codigo == 2
    assert "erro:" in capsys.readouterr().err


def test_mapa_invalido_retorna_codigo_2(capsys, tmp_path):
    mapa = tmp_path / "mapa.yaml"
    mapa.write_text("trechos: []", encoding="utf-8")
    assert main(["analisar", "--mapa", str(mapa), "--deteccoes", DETECCOES]) == 2
    assert "erro:" in capsys.readouterr().err


def test_sem_subcomando_falha():
    with pytest.raises(SystemExit):
        main([])
