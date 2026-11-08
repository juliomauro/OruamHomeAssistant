# 2. API access and scripts

Almost everything in this guide was done by script, calling the HA API, not by clicking in the interface. That makes it possible to rebuild from scratch, keep it under version control and review before applying.

## 2.1 Long-lived token

1. In the interface: **Profile > Security > Long-lived access tokens > Create token**.
2. Save the token in a protected file on the server:

```bash
mkdir -p /DATA/AppData/.secrets/ha-tools && chmod 700 /DATA/AppData/.secrets
nano /DATA/AppData/.secrets/ha_token   # paste the token, save
chmod 600 /DATA/AppData/.secrets/ha_token
```

Copy the `scripts/` folder of this repository to `/DATA/AppData/.secrets/ha-tools/`.

## 2.2 Two ways to talk to HA

### REST (`/api/...`)

The scripts `rede_flows.py`, `rede_automacoes.py`, `telegram_automacoes.py` and `energia.py` use REST. They read the `HA_URL` variable, which defaults to `http://127.0.0.1:8123`:

```bash
cd /DATA/AppData/.secrets/ha-tools
HA_URL=http://192.168.0.240:8123 python3 rede_flows.py "$(cat ../ha_token)"
```

Endpoints used:

| Endpoint | Purpose |
|---|---|
| `POST /api/config/config_entries/flow` and `/flow/{id}` | Create integrations (config flow) without the interface |
| `POST /api/config/automation/config/{id}` | Create or replace an automation |
| `POST /api/template` | Test a Jinja template before using it |
| `POST /api/services/<domain>/<service>` | Call an action |

### WebSocket (`/api/websocket`)

The entity and device registries and the dashboards exist only on the WebSocket API. `ha_ws.py` reads the token on the first stdin line, then a JSON list of commands. It runs **inside** the container, which already has `aiohttp`:

```bash
{ cat ../ha_token; echo; echo '[{"type":"config/entity_registry/list"}]'; } \
  | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

The `echo` after `cat` is required: if the token file does not end with a newline, the token and the JSON stick together and HA answers `auth_invalid`.

The dashboard generators print the commands, which then go through `ha_ws.py`:

```bash
{ cat ../ha_token; echo; python3 painel_casa.py; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

WebSocket commands used:

| Command | Purpose |
|---|---|
| `config/entity_registry/list` / `update` | Rename (`new_entity_id`, `name`), enable (`disabled_by: null`) |
| `config/device_registry/update` | `name_by_user`, `area_id` |
| `lovelace/dashboards/create` | Create a dashboard (the `url_path` must contain a hyphen) |
| `lovelace/config/save` | Save the dashboard configuration |
| `recorder/import_statistics` | Import history (energy) |
| `trace/list` / `trace/get` | Find out why an automation failed |

## 2.3 Editing configuration.yaml

`configuration.yaml` belongs to root inside the container. The safe flow is:

```bash
# 1. backup
docker exec homeassistant cp /config/configuration.yaml /config/configuration.yaml.bak-topic
# 2. build the new file outside the container
docker exec homeassistant cat /config/configuration.yaml > /tmp/cfg.yaml
python3 template_bloco.py /tmp/cfg.yaml chuva ../config/blocos/chuva.yaml > /tmp/cfg.new
# 3. write and validate
docker exec -i homeassistant sh -c 'cat > /config/configuration.yaml' < /tmp/cfg.new
docker exec homeassistant python3 -m homeassistant --script check_config -c /config
# 4. reload (template:, rest: and automations reload without a restart)
```

To reload, use **Developer tools > YAML**, or call the actions `template.reload`, `rest.reload` and `automation.reload`.

`template_bloco.py` keeps each sensor between `  # BLOCO <name>` and `  # FIM <name>` inside `template:`. Running it again replaces the block instead of duplicating it.

## 2.4 Script list

| Script | What it does | Guide |
|---|---|---|
| `ha_ws.py` | Generic WebSocket client | this one |
| `template_bloco.py` | Inserts or replaces a named block in `template:` | [7](07-template-sensors.md) |
| `agenda_template.py` | Inserts the `sensor.agenda_hoje` sensor | [7](07-template-sensors.md) |
| `energia.py`, `historico_tomada.py` | Energy meters and cost, history import | [4](04-energy.md) |
| `boreas_entities.py` | Renames the Glances entities of `boreas` | [3](03-integrations.md) |
| `rede_flows.py`, `rede_rename.py` | Ping, Speedtest and public IP | [5](05-network.md) |
| `deco_rename.py`, `deco_nomes.py` | Standardizes Deco entities and names devices by MAC | [5](05-network.md) |
| `rede_automacoes.py` | New device and observer on Wi-Fi alerts | [5](05-network.md) |
| `lan_scan.py` | Finds routers and the modem on the LAN (HTTP title and SSDP) | [5](05-network.md) |
| `mesh_rename.py`, `corescope_rest.py` | MeshCore and CoreScope | [6](06-meshcore.md) |
| `painel_casa.py`, `painel_tablet.py` | Dashboards | [8](08-dashboards.md) |
| `telegram_automacoes.py` | All Telegram automations | [9](09-telegram.md) |

The scripts use the entity names of my house. Before running one, open it and adjust the lists at the top, which hold the lights, sensors and MACs.

Script comments and generated labels are in Portuguese. Common words: `rede` network, `luzes` lights, `porta` door, `agenda` calendar, `painel` dashboard, `nomes` names, `chuva` rain, `noite` night, `bloco` block.
