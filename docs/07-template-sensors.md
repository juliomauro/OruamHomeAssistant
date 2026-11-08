# 7. Template sensors

The sensors below are **trigger-based templates**: they run an action (for example `calendar.get_events`) and store the result in attributes. They feed the tablet dashboard and the Telegram bot.

All of them live inside `template:` in `configuration.yaml`. The full file is in [`config/configuration-template.yaml`](../config/configuration-template.yaml), and the standalone blocks are in [`config/blocos/`](../config/blocos/).

To insert or update a block:

```bash
docker exec homeassistant cp /config/configuration.yaml /config/configuration.yaml.bak-chuva
docker exec homeassistant cat /config/configuration.yaml > /tmp/cfg.yaml
python3 template_bloco.py /tmp/cfg.yaml chuva ../config/blocos/chuva.yaml > /tmp/cfg.new
docker exec -i homeassistant sh -c 'cat > /config/configuration.yaml' < /tmp/cfg.new
# Developer tools > YAML > Template entities
```

## `sensor.agenda_hoje` (today's agenda)

- **Triggers:** every 10 min, on HA start and on the `agenda_atualizar` event. The bot fires this event before answering `/agenda`.
- **Action:** `calendar.get_events` on several calendars, from today 00:00 until 2 days later.
- **State:** number of events today.
- **Attribute `eventos`:** list of `{ts, te, dia_todo, titulo, agenda}` (start, end, all day, title, calendar), sorted by `ts`.

Sort by **timestamp** (`ts`), not by the date text. Calendars like the F1 one come in UTC and break text sorting.

Install with its own script (same result as a block):

```bash
python3 agenda_template.py /tmp/cfg.yaml > /tmp/cfg.new
```

Edit the list of `calendar.*` inside the script.

## `binary_sensor.chuva_chegando` (rain coming, block `chuva`)

- Every 20 min, reads the **hourly** forecast of `weather.casa` with `weather.get_forecasts`.
- Turns `on` if any of the next 3 hours has 0.5 mm of precipitation or more, or the condition `pouring` or `lightning-rainy`.
- Attributes: `inicio` (HH:MM of the first rainy hour) and `mm_3h` (forecast total).

## `sensor.diario_da_noite` (night log, block `noite`)

Records what happens between 22:00 and 08:00, for the Telegram "good morning" message:

- front door opened;
- internet went down (after 2 min) and came back;
- Deco offline for 3 min;
- new device on the Wi-Fi.

The `eventos` attribute keeps `"HH:MM text"` strings, 20 at most. The sensor resets at 08:05.

The trick is `this.attributes.eventos`: each trigger reads the sensor's own previous list and appends one item.

## `sensor.mesh_ultima_mensagem` (last mesh message)

Triggered by the `meshcore_message` event. The state is `sender: text`, and the `mensagens` attribute keeps the last 15 messages, with time, sender, channel, text, whether it was outgoing and the hop count.

## Testing a template

Before putting a template in a card or automation, test it in **Developer tools > Template**, or through the API:

```bash
curl -s -H "Authorization: Bearer $(cat ../ha_token)" -H 'Content-Type: application/json' \
  -d '{"template":"{{ state_attr(\"sensor.agenda_hoje\",\"eventos\") | count }}"}' \
  http://127.0.0.1:8123/api/template
```

Templates that use `trigger.*` do not run outside an automation. To test those, trigger the automation and look at the trace.
