"""Shared synthetic fixtures. Plates use the FAKE0NN pattern, which is not a valid Brazilian plate."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from olhovivo.mapa import Mapa
from olhovivo.modelos import Deteccao, Regra, Trecho

T0 = datetime(2026, 1, 5, 8, 0, 0)
EXEMPLOS = Path(__file__).resolve().parent.parent / "examples"

# Box centres that fall inside each stretch of the ``mapa`` fixture.
CAIXAS = {
    "rot-2h": (100.0, 60.0, 200.0, 140.0),
    "carga": (620.0, 60.0, 720.0, 140.0),
    "proibido": (100.0, 260.0, 200.0, 340.0),
    "pisca": (320.0, 260.0, 420.0, 340.0),
    "pisca-30": (620.0, 260.0, 720.0, 340.0),
    "fora": (2000.0, 2000.0, 2100.0, 2100.0),
}


@pytest.fixture
def mapa() -> Mapa:
    return Mapa(
        [
            Trecho("rot-2h", "Rotativo 2h", Regra.ROTATIVO, (0, 0, 300, 200), 120),
            Trecho("carga", "Carga e descarga", Regra.CARGA_DESCARGA, (600, 0, 900, 200), 30),
            Trecho("proibido", "Proibido", Regra.PROIBIDO, (0, 200, 300, 400)),
            Trecho("pisca", "So pisca", Regra.SO_PISCA, (300, 200, 600, 400)),
            Trecho("pisca-30", "So pisca 30 min", Regra.SO_PISCA, (600, 200, 900, 400), 30),
        ]
    )


def estadia(
    trecho: str,
    minutos: float,
    *,
    track: str = "t1",
    placa: str | None = "FAKE001",
    pisca: bool | None = None,
    inicio: datetime = T0,
) -> list[Deteccao]:
    """Two detections of the same track in one stretch, ``minutos`` apart."""
    return [
        Deteccao(track, CAIXAS[trecho], inicio, placa, pisca),
        Deteccao(track, CAIXAS[trecho], inicio + timedelta(minutes=minutos), placa, pisca),
    ]
