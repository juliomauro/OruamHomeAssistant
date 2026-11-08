# 0. Inventory

What exists in the house and what was integrated into Home Assistant. **Names, IPs and keys in this repository are fictitious**: the structure is real, the data is not.

## Network and servers

| Item | Name in the guide | IP | Role |
|---|---|---|---|
| ISP modem | Modem | 192.168.0.1 | Fiber, DHCP for the house. UPnP off |
| Main Wi-Fi mesh router | Deco Sala (living room) | 192.168.0.10 | TP-Link Deco M4R |
| Secondary Wi-Fi mesh router | Deco Office | 192.168.0.13 | TP-Link Deco M4R, wired backhaul |
| Main server | `atlas` | 192.168.0.240 | ZimaOS. Runs HA, Traefik, Pi-hole, Plex, Transmission and a self-hosted backlog app |
| Secondary server | `boreas` | 192.168.0.241 | Ubuntu. Runs Glances, Docker for tests and is the Tailscale subnet router |

## Devices

| Category | Devices | How they reach HA |
|---|---|---|
| Lights | Living room: Principal, Atelier, Dining table, Side, Counter, Stairs LED. Office: Ceiling, LED. Backyard: Side, Back. One RGB bulb | Tuya (cloud) |
| Plugs | Office desk plug (with energy metering), counter plug | Tuya |
| Sensors | Front door, motion (PIR) on the stairs, kitchen temperature and humidity | Tuya |
| Robot vacuum | "Rubi" | Tuya |
| IR remote | Universal remote (volume, Blu-ray, ceiling fan) | Tuya, as scenes |
| Camera | Living room IP camera (192.168.0.51) | Generic Camera (RTSP) |
| Audio | Atelier speaker, smart clock in the bedroom, "Toda casa" (whole house) group | Google Cast |
| TV | TV and a streaming stick | Wi-Fi only (named by MAC) |
| 3D printer | Printer with OctoPrint (192.168.0.23) | OctoPrint |
| LoRa radio | MeshCore Wi-Fi companion (192.168.0.40) and repeater/observer REP-CASA-4387 (192.168.0.27) | MeshCore (community) |
| Tablet | Android tablet in the living room, with the "Central" dashboard | Browser / HA app |
| Others | Several Tuya and ESP modules without a final name (`wifi_tuya_*`, `wifi_esp_*`) | Wi-Fi only |

## Integrations

| Integration | Type | Purpose | Guide |
|---|---|---|---|
| Tuya | Built-in (cloud) | Lights, plugs, sensors, vacuum, IR | [3](03-integrations.md#tuya-smart-life) |
| Google Cast | Built-in | Speakers and TTS | [3](03-integrations.md#google-cast) |
| Generic Camera | Built-in | RTSP camera | [3](03-integrations.md#camera) |
| OctoPrint | Built-in | 3D printer | [3](03-integrations.md#octoprint-3d-printer) |
| System Monitor | Built-in | Health of `atlas` | [3](03-integrations.md#servers) |
| Glances | Built-in | Health of `boreas` | [3](03-integrations.md#servers) |
| Pi-hole, Transmission, Plex | Built-in | Services on `atlas` | [3](03-integrations.md#pi-hole-transmission-plex) |
| Google Calendar, Google Drive, Google Gemini | Built-in (OAuth) | Agenda, backup target, AI Assist | [3](03-integrations.md#google) |
| Certificate Expiry | Built-in | Wildcard certificate expiry | [3](03-integrations.md#traefik-and-stacklog-yaml-rest) |
| RESTful (`rest:`) | YAML | Traefik, self-hosted backlog, CoreScope | [3](03-integrations.md#traefik-and-stacklog-yaml-rest), [6](06-meshcore.md) |
| Integral (Riemann), Utility Meter, Template, Number | Helpers | Energy consumption and cost | [4](04-energy.md) |
| Ping, Speedtest.net, DNS IP | Built-in | Internet and outages | [5](05-network.md) |
| TP-Link Deco (`amosyuen/ha-tplink-deco`) | Community (manual) | Wi-Fi mesh and connected devices | [5](05-network.md#53-tp-link-deco-wi-fi-mesh) |
| MeshCore (`meshcore-dev/meshcore-ha`) | Community (Marketplace) | LoRa mesh radio | [6](06-meshcore.md) |
| Telegram bot | Built-in (polling) | Alerts and commands | [9](09-telegram.md) |
| Marketplace: Mushroom, mini-graph-card, card-mod | Cards | Dashboards | [8](08-dashboards.md) |

## Sensors created

| Sensor | What it is | Guide |
|---|---|---|
| `sensor.agenda_hoje` | Today's and tomorrow's events | [7](07-template-sensors.md) |
| `binary_sensor.chuva_chegando` | Rain in the next 3 hours | [7](07-template-sensors.md) |
| `sensor.diario_da_noite` | What happened between 22:00 and 08:00 | [7](07-template-sensors.md) |
| `sensor.mesh_ultima_mensagem` | Last 15 mesh messages | [7](07-template-sensors.md) |
| `binary_sensor.rede_*`, `sensor.rede_*`, `sensor.internet_*` | Internet, latency, speedtest, public IP | [5](05-network.md) |
| `sensor.deco_*`, `device_tracker.wifi_*` | Decos and Wi-Fi devices | [5](05-network.md) |
| `sensor.setup_escritorio_*`, `sensor.custo_setup_*` | Energy and cost | [4](04-energy.md) |
| `sensor.corescope_*` | MeshCore community nodes | [6](06-meshcore.md) |

## Automations

| Automation | What it does |
|---|---|
| `porta_aberta_madrugada` | Front door opened between 23:30 and 06:00: speaks on the speaker (at 80% volume, then restores the previous volume) and sends a Telegram alert |
| `wifi_aparelho_novo` | Never seen device on the Wi-Fi: HA notification and Telegram message with buttons |
| `observer_wifi` | The repeater/observer joined or left the Wi-Fi |
| `telegram_comandos`, `telegram_botoes_*` | Bot commands and buttons |
| `telegram_internet`, `telegram_deco_offline` | Internet is back, Deco offline |
| `telegram_impressora` | 3D print finished |
| `telegram_chuva` | Rain is coming |
| `telegram_servidores` | Disk, temperature, server down, Traefik, Pi-hole, certificate, reboot |
| `telegram_bom_dia` | Daily summary at 07:30 |

## Dashboards

| Dashboard | Purpose |
|---|---|
| `painel-casa` | Main dashboard with 7 tabs: Casa (home), Sala (living room), Escritório (office), Externo (outside), Servidores (servers), Rede (network), Mesh |
| `painel-tablet` | Single screen for the living room tablet: clock, agenda, weather, status, lights, audio |
