"""OlhoVivo: decision support for parking enforcement.

The core (street rules, dwell time, infraction decision) is deterministic and
has no dependency on network access or on a vision model. Detections come in
through the ``FonteDeteccao`` protocol. The output is an alert for a human
traffic agent to review; nothing here issues a fine.
"""

from olhovivo.fonte import FonteDeteccao, FonteFake, carregar_deteccoes
from olhovivo.mapa import Mapa, carregar_mapa
from olhovivo.modelos import Deteccao, ErroEntrada, Infracao, Regra, Trecho, Veiculo
from olhovivo.pipeline import analisar
from olhovivo.relatorio import montar_relatorio

__version__ = "0.1.0"

__all__ = [
    "Deteccao",
    "ErroEntrada",
    "FonteDeteccao",
    "FonteFake",
    "Infracao",
    "Mapa",
    "Regra",
    "Trecho",
    "Veiculo",
    "analisar",
    "carregar_deteccoes",
    "carregar_mapa",
    "montar_relatorio",
]
