# 7. Sensores de template

Os sensores abaixo são **trigger-based templates**: rodam uma ação (Ex: `calendar.get_events`) e guardam o resultado em atributos. Eles alimentam o painel do tablet e o bot do Telegram.

Todos ficam dentro de `template:` no `configuration.yaml`. O arquivo completo está em [`config/configuration-template.yaml`](../../config/configuration-template.yaml), e os blocos avulsos em [`config/blocos/`](../../config/blocos/).

Para inserir ou atualizar um bloco:

```bash
docker exec homeassistant cp /config/configuration.yaml /config/configuration.yaml.bak-chuva
docker exec homeassistant cat /config/configuration.yaml > /tmp/cfg.yaml
python3 template_bloco.py /tmp/cfg.yaml chuva ../config/blocos/chuva.yaml > /tmp/cfg.novo
docker exec -i homeassistant sh -c 'cat > /config/configuration.yaml' < /tmp/cfg.novo
# Ferramentas de desenvolvedor > YAML > Entidades de template
```

## `sensor.agenda_hoje`

- **Gatilhos:** a cada 10 min, na partida do HA e no evento `agenda_atualizar`. O bot dispara esse evento antes de responder `/agenda`.
- **Ação:** `calendar.get_events` em várias agendas, de hoje 00:00 até daqui a 2 dias.
- **Estado:** número de eventos de hoje.
- **Atributo `eventos`:** lista de `{ts, te, dia_todo, titulo, agenda}`, ordenada por `ts`.

Ordene pelo **timestamp** (`ts`), não pelo texto da data. Agendas como a da F1 vêm em UTC e quebram a ordenação por texto.

Instalação com script próprio (equivalente a um bloco):

```bash
python3 agenda_template.py /tmp/cfg.yaml > /tmp/cfg.novo
```

Edite a lista de `calendar.*` dentro do script.

## `binary_sensor.chuva_chegando` (bloco `chuva`)

- A cada 20 min, lê a previsão **horária** do `weather.casa` com `weather.get_forecasts`.
- Fica `on` se alguma das próximas 3 horas tiver precipitação de 0,5 mm ou mais, ou condição `pouring` ou `lightning-rainy`.
- Atributos: `inicio` (HH:MM da primeira hora com chuva) e `mm_3h` (soma prevista).

## `sensor.diario_da_noite` (bloco `noite`)

Anota o que acontece entre 22h e 8h, para o "bom dia" do Telegram:

- porta de entrada aberta;
- internet caiu (depois de 2 min fora) e voltou;
- Deco offline por 3 min;
- aparelho novo no Wi-Fi.

O atributo `eventos` guarda textos `"HH:MM texto"`, no máximo 20. O sensor zera às 08:05.

O truque é o `this.attributes.eventos`: cada disparo lê a lista anterior do próprio sensor e acrescenta um item.

## `sensor.mesh_ultima_mensagem`

Disparado pelo evento `meshcore_message`. O estado é `remetente: texto`; o atributo `mensagens` guarda as últimas 15 mensagens, com hora, remetente, canal, texto, se é de saída e o número de saltos.

## Testando um template

Antes de colocar um template em um card ou automação, teste em **Ferramentas de desenvolvedor > Modelo**, ou pela API:

```bash
curl -s -H "Authorization: Bearer $(cat ../ha_token)" -H 'Content-Type: application/json' \
  -d '{"template":"{{ state_attr(\"sensor.agenda_hoje\",\"eventos\") | count }}"}' \
  http://127.0.0.1:8123/api/template
```

Templates com `trigger.*` não rodam fora de uma automação. Para testar esses, dispare a automação e veja o trace.
