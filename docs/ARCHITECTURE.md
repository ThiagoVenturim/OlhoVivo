# Architecture

OlhoVivo is split in two: a detection source, which is replaceable, and a decision core, which is deterministic and has no I/O beyond reading its two input files.

```
FonteDeteccao --> tracking --> regras --> relatorio
(fonte.py)        (uses mapa)             (alerts for human review)
```

## Why the split

Vision models are heavy, need a GPU or a large download, and give slightly different results across versions. The parking rules are simple and must be exactly right. Keeping them apart means the rules can be tested offline in milliseconds with synthetic data, and a detector can be swapped without touching the logic that decides what counts as an infraction.

The core imports nothing related to vision, video or networking. Its only third-party dependency is PyYAML, for the map file.

## Modules

All under `src/olhovivo/`.

| Module | Responsibility |
| --- | --- |
| `modelos.py` | Frozen dataclasses: `Deteccao`, `Trecho`, `Veiculo`, `Infracao`, the `Regra` enum, and `ErroEntrada`. |
| `fonte.py` | The `FonteDeteccao` protocol, `FonteFake`, and the JSON loader for detections. |
| `mapa.py` | `Mapa`, the YAML loader, and the detection-to-stretch lookup. |
| `tracking.py` | Groups detections by `id_track` and splits each track into stays (`Permanencia`). |
| `regras.py` | Decides whether a stay breaks the rule of its stretch. Pure functions. |
| `pipeline.py` | `analisar`: drains a source, measures stays, applies the rules. |
| `relatorio.py` | Turns infractions into the alert report (dict, JSON or text). |
| `cli.py` | `olhovivo analisar`. |

## Data flow

1. A source yields `Deteccao` objects: track id, bounding box, timestamp, and optionally a plate and whether hazard lights were on.
2. `Mapa.trecho_de` assigns each detection to the stretch whose rectangle contains the centre of the box, or to none.
3. `medir_permanencias` sorts each track by timestamp and cuts it into stays. A stay ends when the next detection is in another stretch, outside every stretch, or later than `lacuna_max` after the previous one.
4. `avaliar` compares one stay with the rule of its stretch and returns an `Infracao` or `None`.
5. `montar_relatorio` formats the infractions as alerts with status `pendente_revisao_humana`.

Output order is fixed: by start time, then track id, then stretch id. The order of the input does not change the result.

## The detection interface

```python
class FonteDeteccao(Protocol):
    def proximas(self) -> list[Deteccao]: ...
```

`proximas` returns the next batch. An empty list means the source is finished. `analisar` calls it until that happens, so the current design is batch analysis of a finite recording, not a live stream.

`FonteFake` takes a list of detections and replays it, all at once or in batches of a given size. It is used by the tests, by the CLI (fed from the JSON file) and by the demo.

A real source would wrap a video reader, a detector, a tracker and a plate reader, and emit `Deteccao` objects. What it must guarantee:

- `id_track` is stable for the same vehicle while it is in view. The core does no re-identification.
- `timestamp` is the capture time of the frame, with all detections either timezone-aware or all naive.
- `bbox` is in the same pixel coordinates as the areas in the map.
- `tem_pisca` is `None` when the source cannot tell. Do not default it to `False`: for the `so_pisca` rule, `False` is evidence against the driver and `None` is absence of evidence.

No such source exists in this repository.

## Decisions and their limits

**"Stopped" is a duration, not a motion estimate.** A vehicle counts as stopped when its stay in a stretch lasts at least `parado_min` (60 seconds by default). A vehicle crawling through a no-parking stretch in slow traffic for more than a minute would be flagged. A real source could avoid this by only emitting detections for stationary vehicles.

**Stays are bounded by detections.** The duration is the time between the first and the last detection in the stretch. A single detection is a stay of zero seconds and never triggers a rule.

**No gap limit by default.** With `lacuna_max` unset, two detections of the same track in the same stretch hours apart count as one stay, as long as no detection in between puts the vehicle elsewhere. This suits sparse synthetic data. With a real tracker, set a limit.

**Areas are axis-aligned rectangles, matched by box centre.** Real kerbs seen from a camera are skewed quadrilaterals, and the point where a vehicle touches the ground is closer to the bottom of its box than to the centre. Polygons and a ground-contact point are on the roadmap.

**One rule per stretch, no schedule.** Real signs often apply only on certain days and hours. The map has no notion of time of day yet, so a rule is treated as always in force.

**Plate per track is the most frequent reading**, with ties broken alphabetically. There is no validation of plate format.

**Hazard lights are summarised per stay**: on if seen on at least once, off if only ever seen off, unknown otherwise.

## Human in the loop

Nothing in the code issues a fine, writes to an enforcement system or contacts anyone. The report starts with a notice that the alerts are not fines, and each alert carries the status `pendente_revisao_humana`. Tests assert both. Changes that weaken this are out of scope for the project.

## Privacy

Plates are personal data. The repository holds only synthetic plates in the `FAKE0NN` pattern, and a test checks that the example file contains nothing else. The report keeps the plate because the agent needs it to review the case; `--mascarar-placas` hides most of it for logs or shared output. Storage, retention and blurring of images are the responsibility of the future detection source and of whoever deploys the system; see the ethics section of the README.
