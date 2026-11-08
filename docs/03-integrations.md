# 3. Integrations

All of them were added in **Settings > Devices & services > Add integration**, except the ones marked as YAML.

## Tuya (Smart Life)

I use the official Tuya integration, through the cloud: in the Smart Life app, go to **Me > Settings > Account** and scan the QR code that HA shows.

What came in:

- living room, office and backyard switches (`switch.*`);
- door sensor (`binary_sensor.entrada_porta_de_entrada_porta`);
- stairs PIR;
- kitchen thermometer;
- plug with energy metering;
- robot vacuum (`vacuum.sala_de_estar_rubi`);
- IR scenes (`scene.*`).

Tips:

- The names of each key of multi-key switches set in the app do **not** reach HA. Rename them in HA.
- Keys not wired to anything can be disabled in the entity settings.
- Future plan: move to Tuya Local, which works without the cloud and needs the local keys from a Tuya developer account.

## Google Cast

The integration discovers the speakers and displays by itself: Som atelier, Relógio suíte (smart clock) and the "Toda casa" group. The TTS used in automations is `tts.google_translate_en_com` with `language: pt-br`.

## OctoPrint (3D printer)

- Host: 192.168.0.23.
- **Turn off the webcam in OctoPrint** if there is none. With the webcam enabled and not answering, the whole integration fails.
- Entities used: `binary_sensor.escritorio_octoprint_printing`, `sensor.escritorio_octoprint_job_percentage`, `_estimated_finish_time`, `_current_file`, `_current_state`.

## Servers

| Server | Integration | Entities |
|---|---|---|
| atlas (HA itself) | System Monitor | `sensor.atlas_*` (CPU, memory, disk, `atlas_4tb`, temperature, `atlas_ligado_desde` = up since) |
| boreas | Glances | `sensor.boreas_*` |

On `boreas`, Glances runs in web mode, listening only on the LAN IP:

```bash
glances -w --disable-webui -B 192.168.0.241 -p 61208
```

The integration creates dozens of sensors with names like `sensor.192_168_0_241_cpu_usage`. `boreas_entities.py` generates the commands that rename the useful ones to `sensor.boreas_cpu`, `boreas_temperatura`, `boreas_disco` and so on, and disable the rest:

```bash
{ cat ../ha_token; echo; echo '[{"type":"config/entity_registry/list"}]'; } \
  | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)" > list.json
python3 boreas_entities.py < list.json > cmds.json
{ cat ../ha_token; echo; cat cmds.json; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

## Pi-hole, Transmission, Plex

- **Pi-hole:** `sensor.pihole_*` and `switch.pihole`, which turns blocking on and off.
- **Transmission:** `sensor.transmission_*` and `switch.transmission`.
- **Plex:** the integration asks for a plex.tv login. It creates `sensor.plex_assistindo` (how many people are watching now) and one sensor per library.

## Google

The three integrations use **the same OAuth client**:

1. In Google Cloud Console, create a project and enable the **Google Calendar**, **Google Drive** and **Generative Language** APIs.
2. Create an **OAuth client ID** credential of type **Web application**, with the redirect URI `https://my.home-assistant.io/redirect/oauth`.
3. In HA, under **Settings > Devices & services > ⋮ > Application credentials**, register the client ID and secret.
4. Add **Google Calendar** and **Google Drive** and sign in.

| Integration | Use |
|---|---|
| Google Calendar | One `calendar.*` per calendar. I use personal, family, birthdays, holidays, school and F1 |
| Google Drive | Target of the automatic backup |
| Google Gemini (Generative AI) | Assist pipeline in pt-BR. Needs prepaid credit in AI Studio, otherwise it returns error 402 |

## Camera

The living room camera comes in as **Generic Camera**, with the RTSP stream `rtsp://192.168.0.51:554/av_stream/ch0` (generic IP camera).

The snapshot (still image) still fails with error 500 because of sparse keyframes in the stream. The live video works.

## Traefik and Stacklog (YAML, `rest:`)

These two services have no integration of their own, so I read their APIs with `rest:` in `configuration.yaml`. The full snippet is in [`config/configuration-rest.yaml`](../config/configuration-rest.yaml).

| Sensor | Source |
|---|---|
| `binary_sensor.traefik_online`, `sensor.traefik_rotas/servicos/problemas` (routes, services, problems) | `https://traefik.example.com/api/overview`, every 60 s |
| `sensor.stacklog_abertas`, `_concluidas_hoje`, `_ultima_concluida`, `_concluidas_7_dias`, `_observacoes`, `_projetos_ativos` (open, done today, last done, done in 7 days, notes, active projects) | Stacklog API, every 5 min, read only |

The certificate is tracked by the **Certificate Expiry** integration (`cert_expiry`), pointing to `ha.example.com:443`, which creates `sensor.traefik_certificado`.

After adding or changing `rest:` blocks, run the `rest.reload` action. No restart needed.
