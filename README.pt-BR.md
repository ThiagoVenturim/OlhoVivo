# OlhoVivo

[Read in English](README.md)

O OlhoVivo confere veículos estacionados contra a regra de cada trecho da via: rotativo com limite de tempo (2h, 5h), proibido estacionar, carga e descarga e parada só com pisca-alerta. Ele recebe as detecções dos veículos, um mapa com as regras e o tempo que cada veículo ficou no trecho, e devolve uma lista de alertas para o agente de trânsito revisar.

É apoio à decisão. O OlhoVivo nunca autua. Todo alerta sai marcado como `pendente_revisao_humana`, e só a autoridade de trânsito (o Detran e seus agentes) decide o que fazer com ele.

## Estado atual

MVP. O núcleo de decisão está pronto e testado: regras, tempo de permanência, relatório e linha de comando. Ainda não há visão computacional neste repositório. As detecções entram por uma interface (`FonteDeteccao`), e a única implementação incluída é a `FonteFake`, que reproduz uma lista pronta. Rodar detector, leitor de placa e tracker de verdade sobre vídeo é o próximo passo e está descrito no roadmap abaixo.

## Como rodar a demo offline

Precisa de Python 3.11 ou mais novo. Não usa rede nem baixa modelo nenhum.

```
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -e .[dev]
olhovivo analisar --mapa examples/mapa.yaml --deteccoes examples/deteccoes.json
```

O exemplo tem nove veículos sintéticos. Quatro deles descumprem a regra do trecho e aparecem na saída:

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

A saída do programa não usa acentos de propósito, para não quebrar em terminais com codificação antiga.

Opções de `olhovivo analisar`:

| Opção | O que faz |
| --- | --- |
| `--formato texto\|json` | Formato da saída. Padrão `texto`. |
| `--parado-segundos N` | Permanência mínima para o veículo contar como parado, e não de passagem. Padrão 60. |
| `--lacuna-max-segundos N` | Um intervalo sem detecção maior que esse encerra a permanência. Padrão: sem limite. |
| `--mascarar-placas` | Mostra só os três primeiros caracteres de cada placa. |

O código de saída é 0 quando a análise rodou, com ou sem alertas, e 2 quando o mapa ou o arquivo de detecções é inválido.

## As regras

| Regra (`regra`) | Gera alerta quando |
| --- | --- |
| `rotativo` | a permanência passa de `janela_minutos` |
| `carga_descarga` | a permanência passa de `janela_minutos` |
| `proibido` | o veículo está parado (permanência de pelo menos `--parado-segundos`) |
| `so_pisca` | o veículo está parado e o pisca-alerta foi visto desligado |

Detalhes que fazem diferença:

- Permanência exatamente igual à janela está dentro da regra. Um segundo a mais já não está.
- O pisca-alerta pisca, então basta uma detecção com ele ligado para considerar ligado naquela permanência.
- Se a fonte nunca informa o pisca (`tem_pisca` nulo), `so_pisca` não gera alerta. Não há evidência para nenhum dos lados, e a ferramenta não presume contra o motorista.
- Um trecho `so_pisca` também pode ter `janela_minutos`. Passar desse tempo gera alerta mesmo com o pisca ligado.
- Quem sai do trecho e volta começa uma permanência nova. O tempo não é somado.

## Arquivos de entrada

O mapa é um YAML. Cada trecho tem um retângulo em pixels do quadro, `[x1, y1, x2, y2]`. A detecção pertence ao trecho que contém o centro da sua caixa; se as áreas se sobrepõem, vale o primeiro trecho da lista.

```yaml
trechos:
  - id: rot-2h
    nome: Rua Ficticia, lado par (rotativo 2h)
    regra: rotativo
    janela_minutos: 120
    area: [0, 0, 300, 200]
```

As detecções são um JSON: uma lista, ou um objeto com a lista em `deteccoes`. `placa` e `tem_pisca` são opcionais. O timestamp é ISO 8601.

```json
{"id_track": "t1", "placa": "FAKE001", "bbox": [100, 60, 200, 140], "timestamp": "2026-01-05T08:00:00", "tem_pisca": false}
```

## Uso como biblioteca

```python
from olhovivo import FonteFake, analisar, carregar_deteccoes, carregar_mapa, montar_relatorio

mapa = carregar_mapa("examples/mapa.yaml")
fonte = FonteFake(carregar_deteccoes("examples/deteccoes.json"))
relatorio = montar_relatorio(analisar(fonte, mapa))
```

Qualquer objeto com um método `proximas() -> list[Deteccao]` pode entrar no lugar da `FonteFake`. Veja [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Aviso ético e LGPD

Leia antes de apontar a ferramenta para uma câmera de verdade.

- Placa de veículo é dado pessoal pela LGPD (Lei 13.709/2018). Imagem com pessoas identificáveis também.
- Este repositório não tem dado real. Todas as placas dos testes e exemplos seguem o padrão `FAKE0NN`, que não é um formato válido de placa brasileira. Não faça commit de placas, imagens ou vídeos reais.
- O uso real exige base legal para o tratamento, definida pelo órgão público responsável. Fiscalizar é atribuição da autoridade de trânsito; um particular que rode isto numa via pública não ganha poder de autuar ninguém.
- Colete o mínimo: a placa e os horários necessários para o alerta, não a gravação contínua da rua.
- Guarde os dados por um prazo curto e definido, e apague depois. Veículo que não descumpriu regra não deve ficar armazenado.
- Borre rostos e pessoas em qualquer imagem guardada como evidência.
- Quem decide é uma pessoa. O alerta pode estar errado: placa lida errado, tracker que troca dois veículos, câmera que não pegou o pisca. O agente precisa confirmar cada caso antes de qualquer providência.

Este texto não é parecer jurídico. A análise legal é responsabilidade de quem implantar o sistema.

## Roadmap

Cada item entra atrás da interface `FonteDeteccao` que já existe, então o núcleo e os testes não mudam.

1. Detecção de veículos nos quadros do vídeo (a opção prevista é um detector da família YOLO).
2. Leitura de placa (ALPR) para preencher `placa`, ficando com a leitura mais frequente de cada track.
3. Tracking de múltiplos objetos (ByteTrack ou DeepSORT são os candidatos) para gerar um `id_track` estável.
4. Detecção de pisca-alerta para preencher `tem_pisca`.
5. Áreas em polígono e calibração de câmera no lugar dos retângulos alinhados aos eixos.
6. Borrar rostos e aplicar uma política de retenção à evidência guardada.

Nada disso está implementado. Os nomes acima são candidatos, não dependências deste pacote.

## Desenvolvimento

```
git config core.hooksPath .githooks
pip install -e .[dev]
ruff check .
python -m pytest
python scripts/check_no_emoji.py
```

Veja [CONTRIBUTING.md](CONTRIBUTING.md). Licença: MIT.
