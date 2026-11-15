# OlhoVivo

[Leia em portugues](README.pt-BR.md)

OlhoVivo checks parked vehicles against the parking rule of each stretch of street: paid rotating parking with a time limit (2h, 5h), no parking, loading and unloading, and hazard-lights-only stops. It takes vehicle detections, a map of the rules and the time each vehicle stayed, and produces a list of alerts for a traffic agent to review.

It is decision support. It never issues a fine. Every alert leaves the tool marked `pendente_revisao_humana` (pending human review), and only the traffic authority (in Brazil, the Detran and its agents) can decide what to do with it.

## Status

MVP. The decision core is complete and tested: rules, dwell time, report, CLI. There is no computer vision in this repository yet. Detections come in through an interface (`FonteDeteccao`), and the only implementation shipped is `FonteFake`, which replays a predefined list. Running a real detector, plate reader and tracker over video is the next step and is described in the roadmap below.

## Run the offline demo

Needs Python 3.11 or newer. No network access and no model download are involved.

```
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -e .[dev]
olhovivo analisar --mapa examples/mapa.yaml --deteccoes examples/deteccoes.json
```

The example has nine synthetic vehicles. Four of them break a rule and show up in the output:

```
Apoio a decisao: estes alertas NAO sao autuacoes. Cada item exige revisao e confirmacao de um agente de transito habilitado antes de qualquer providencia.

Alertas para revisao: 4

[1] placa FAKE001 (track t1)
    trecho:    Rua Ficticia, lado par (rotativo 2h) (rot-2h)
    regra:     rotativo
    inicio:    2026-01-05T08:00:00
    fim:       2026-01-05T10:30:00
    duracao:   150.0 min
    evidencia: permanencia de 150.0 min excede a janela de 120 min do rotativo (3 deteccoes)
    status:    pendente_revisao_humana
...
```

Options of `olhovivo analisar`:

| Option | Meaning |
| --- | --- |
| `--formato texto\|json` | Output format. Default `texto`. |
| `--parado-segundos N` | Minimum stay for a vehicle to count as stopped rather than passing through. Default 60. |
| `--lacuna-max-segundos N` | A gap between detections longer than this ends the stay. Default: no limit. |
| `--mascarar-placas` | Hide all but the first three characters of each plate in the output. |

The exit code is 0 when the analysis ran, with or without alerts, and 2 when the map or the detections file is invalid.

## The rules

| Rule (`regra`) | Alert when |
| --- | --- |
| `rotativo` | the stay is longer than `janela_minutos` |
| `carga_descarga` | the stay is longer than `janela_minutos` |
| `proibido` | the vehicle is stopped (stay of at least `--parado-segundos`) |
| `so_pisca` | the vehicle is stopped and its hazard lights were seen off |

Details that matter:

- A stay exactly equal to the window is within the rule. One second over is not.
- Hazard lights blink, so one detection with them on is enough to treat them as on for that stay.
- If the source never says whether the hazard lights were on (`tem_pisca` null), `so_pisca` raises no alert. There is no evidence either way, and the tool does not guess against the driver.
- A `so_pisca` stretch may also set `janela_minutos`. Staying longer than that raises an alert even with hazard lights on.
- A vehicle that leaves a stretch and comes back starts a new stay. Time is not added up across stays.

## Input files

The map is YAML. Each stretch has a rectangle in frame pixels, `[x1, y1, x2, y2]`. A detection belongs to the stretch that contains the centre of its bounding box; if areas overlap, the first stretch listed wins.

```yaml
trechos:
  - id: rot-2h
    nome: Rua Ficticia, lado par (rotativo 2h)
    regra: rotativo
    janela_minutos: 120
    area: [0, 0, 300, 200]
```

Detections are JSON, either a list or an object with a `deteccoes` list. `placa` and `tem_pisca` are optional. Timestamps are ISO 8601.

```json
{"id_track": "t1", "placa": "FAKE001", "bbox": [100, 60, 200, 140], "timestamp": "2026-01-05T08:00:00", "tem_pisca": false}
```

## Use as a library

```python
from olhovivo import FonteFake, analisar, carregar_deteccoes, carregar_mapa, montar_relatorio

mapa = carregar_mapa("examples/mapa.yaml")
fonte = FonteFake(carregar_deteccoes("examples/deteccoes.json"))
relatorio = montar_relatorio(analisar(fonte, mapa))
```

Any object with a `proximas() -> list[Deteccao]` method can replace `FonteFake`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Ethics and data protection (LGPD)

Read this before pointing the tool at a real camera.

- A licence plate is personal data under the Brazilian data protection law (LGPD, Lei 13.709/2018). So is any image with identifiable people in it.
- This repository contains no real data. Every plate in tests and examples follows the `FAKE0NN` pattern, which is not a valid Brazilian plate format. Do not commit real plates, images or video.
- Real use requires a legal basis for the processing, defined by the public body responsible. Enforcement is the traffic authority's job; a private party running this on a public street does not gain any power to fine anyone.
- Collect the minimum: keep the plate and the times needed for the alert, not continuous footage of the street.
- Keep data for a short, defined period and delete it afterwards. Vehicles that broke no rule should not be stored.
- Blur faces and bystanders in any image kept as evidence.
- A person decides. The alerts can be wrong: a misread plate, a tracker that swaps two vehicles, a camera that missed the hazard lights. An agent has to confirm each case before anything is done.

This text is not legal advice. Whoever deploys the system is responsible for the legal review.

## Roadmap

Each item goes behind the existing `FonteDeteccao` interface, so the core and its tests do not change.

1. Vehicle detection over video frames (a YOLO-family detector is the planned option).
2. Plate reading (ALPR) to fill `placa`, keeping the most frequent reading per track.
3. Multi-object tracking (ByteTrack or DeepSORT are the candidates) to produce a stable `id_track`.
4. Hazard-light detection to fill `tem_pisca`.
5. Polygon areas and camera calibration instead of axis-aligned rectangles.
6. Face blurring and a retention policy applied to stored evidence.

None of these is implemented. The names above are candidates, not dependencies of this package.

## Development

```
git config core.hooksPath .githooks
pip install -e .[dev]
ruff check .
python -m pytest
python scripts/check_no_emoji.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Licence: MIT.
