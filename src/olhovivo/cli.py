"""Command line: ``olhovivo analisar --mapa mapa.yaml --deteccoes deteccoes.json``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import timedelta

from olhovivo import __version__
from olhovivo.fonte import FonteFake, carregar_deteccoes
from olhovivo.mapa import carregar_mapa
from olhovivo.modelos import ErroEntrada
from olhovivo.pipeline import analisar
from olhovivo.regras import PARADO_MIN_PADRAO
from olhovivo.relatorio import formatar_json, formatar_texto, montar_relatorio


def _segundos_nao_negativos(texto: str) -> float:
    valor = float(texto)
    if valor < 0:
        raise argparse.ArgumentTypeError("deve ser maior ou igual a zero")
    return valor


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="olhovivo",
        description=(
            "Apoio a decisao para fiscalizacao de estacionamento. "
            "Gera alertas para revisao humana; nao autua."
        ),
    )
    parser.add_argument("--version", action="version", version=f"olhovivo {__version__}")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("analisar", help="aplica as regras do mapa a um arquivo de deteccoes")
    p.add_argument("--mapa", required=True, help="YAML com os trechos e regras")
    p.add_argument("--deteccoes", required=True, help="JSON com as deteccoes")
    p.add_argument("--formato", choices=("texto", "json"), default="texto")
    p.add_argument(
        "--parado-segundos",
        type=_segundos_nao_negativos,
        default=PARADO_MIN_PADRAO.total_seconds(),
        help="permanencia minima para considerar o veiculo parado (padrao: %(default)s)",
    )
    p.add_argument(
        "--lacuna-max-segundos",
        type=_segundos_nao_negativos,
        default=None,
        help="intervalo sem deteccao que encerra uma permanencia (padrao: sem limite)",
    )
    p.add_argument(
        "--mascarar-placas",
        action="store_true",
        help="oculta parte da placa na saida",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    try:
        mapa = carregar_mapa(args.mapa)
        fonte = FonteFake(carregar_deteccoes(args.deteccoes))
    except (ErroEntrada, OSError) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 2

    lacuna = args.lacuna_max_segundos
    infracoes = analisar(
        fonte,
        mapa,
        parado_min=timedelta(seconds=args.parado_segundos),
        lacuna_max=None if lacuna is None else timedelta(seconds=lacuna),
    )
    relatorio = montar_relatorio(infracoes, mascarar_placas=args.mascarar_placas)
    formatar = formatar_json if args.formato == "json" else formatar_texto
    print(formatar(relatorio))
    return 0


if __name__ == "__main__":
    sys.exit(main())
