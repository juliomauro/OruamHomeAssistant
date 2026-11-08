# 0. Inventário

O que existe na casa e o que foi integrado ao Home Assistant. **Nomes, IPs e chaves deste repositório são fictícios**: a estrutura é a real, os dados não.

## Rede e servidores

| Item | Nome no guia | IP | Papel |
|---|---|---|---|
| Modem da operadora | Modem | 192.168.0.1 | Fibra, DHCP da casa. UPnP desligado |
| Roteador Wi-Fi mesh principal | Deco Sala | 192.168.0.10 | TP-Link Deco M4R |
| Roteador Wi-Fi mesh secundário | Deco Office | 192.168.0.13 | TP-Link Deco M4R, backhaul por cabo |
| Servidor principal | `atlas` | 192.168.0.240 | ZimaOS. Roda HA, Traefik, Pi-hole, Plex, Transmission e um backlog self-hosted |
| Servidor secundário | `boreas` | 192.168.0.241 | Ubuntu. Roda Glances, Docker de testes e é o subnet router do Tailscale |

## Aparelhos

| Categoria | Aparelhos | Como chega no HA |
|---|---|---|
| Luzes | Sala: Principal, Atelier, Mesa de jantar, Lateral, Balcão, LED da escada. Escritório: Teto, LED. Quintal: Lateral, Fundo. Uma lâmpada RGB | Tuya (nuvem) |
| Tomadas | Tomada do setup do escritório (com medição de energia), tomada do balcão | Tuya |
| Sensores | Porta de entrada, presença (PIR) na escada, temperatura e umidade da cozinha | Tuya |
| Robô aspirador | "Rubi" | Tuya |
| Controle IR | Controle universal (volume, Blu-ray, ventilador de teto) | Tuya, como cenas |
| Câmera | Câmera IP da sala (192.168.0.51) | Generic Camera (RTSP) |
| Som | Som do atelier, relógio smart da suíte, grupo "Toda casa" | Google Cast |
| TV | TV e um aparelho de streaming | Só no Wi-Fi (nomeados pelo MAC) |
| Impressora 3D | Impressora com OctoPrint (192.168.0.23) | OctoPrint |
| Rádio LoRa | Companion MeshCore Wi-Fi (192.168.0.40) e repetidor/observer REP-CASA-4387 (192.168.0.27) | MeshCore (comunidade) |
| Tablet | Tablet Android na sala, com o painel "Central" | Navegador / app do HA |
| Outros | Vários módulos Tuya e ESP sem nome definitivo (`wifi_tuya_*`, `wifi_esp_*`) | Só no Wi-Fi |

## Integrações

| Integração | Tipo | Para quê | Guia |
|---|---|---|---|
| Tuya | Nativa (nuvem) | Luzes, tomadas, sensores, robô, IR | [3](03-integracoes.md#tuya-smart-life) |
| Google Cast | Nativa | Alto-falantes e TTS | [3](03-integracoes.md#google-cast) |
| Generic Camera | Nativa | Câmera RTSP | [3](03-integracoes.md#câmera) |
| OctoPrint | Nativa | Impressora 3D | [3](03-integracoes.md#octoprint-impressora-3d) |
| System Monitor | Nativa | Saúde do `atlas` | [3](03-integracoes.md#servidores) |
| Glances | Nativa | Saúde do `boreas` | [3](03-integracoes.md#servidores) |
| Pi-hole, Transmission, Plex | Nativas | Serviços do `atlas` | [3](03-integracoes.md#pi-hole-transmission-plex) |
| Google Calendar, Google Drive, Google Gemini | Nativas (OAuth) | Agenda, destino do backup, Assist com IA | [3](03-integracoes.md#google) |
| Certificate Expiry | Nativa | Validade do certificado wildcard | [3](03-integracoes.md#traefik-e-stacklog-yaml-rest) |
| RESTful (`rest:`) | YAML | Traefik, backlog self-hosted, CoreScope | [3](03-integracoes.md#traefik-e-stacklog-yaml-rest), [6](06-meshcore.md) |
| Integral (Riemann), Utility Meter, Template, Número | Helpers | Consumo e custo de energia | [4](04-energia.md) |
| Ping, Speedtest.net, DNS IP | Nativas | Internet e quedas | [5](05-rede.md) |
| TP-Link Deco (`amosyuen/ha-tplink-deco`) | Comunidade (manual) | Wi-Fi mesh e aparelhos conectados | [5](05-rede.md#53-tp-link-deco-wi-fi-mesh) |
| MeshCore (`meshcore-dev/meshcore-ha`) | Comunidade (Marketplace) | Rádio LoRa mesh | [6](06-meshcore.md) |
| Telegram bot | Nativa (polling) | Alertas e comandos | [9](09-telegram.md) |
| Marketplace: Mushroom, mini-graph-card, card-mod | Cards | Painéis | [8](08-paineis.md) |

## Sensores criados

| Sensor | O que é | Guia |
|---|---|---|
| `sensor.agenda_hoje` | Eventos de hoje e amanhã | [7](07-sensores-template.md) |
| `binary_sensor.chuva_chegando` | Chuva nas próximas 3 horas | [7](07-sensores-template.md) |
| `sensor.diario_da_noite` | O que aconteceu entre 22h e 8h | [7](07-sensores-template.md) |
| `sensor.mesh_ultima_mensagem` | Últimas 15 mensagens do mesh | [7](07-sensores-template.md) |
| `binary_sensor.rede_*`, `sensor.rede_*`, `sensor.internet_*` | Internet, latência, speedtest, IP público | [5](05-rede.md) |
| `sensor.deco_*`, `device_tracker.wifi_*` | Decos e aparelhos do Wi-Fi | [5](05-rede.md) |
| `sensor.setup_escritorio_*`, `sensor.custo_setup_*` | Energia e custo | [4](04-energia.md) |
| `sensor.corescope_*` | Nós da comunidade MeshCore | [6](06-meshcore.md) |

## Automações

| Automação | O que faz |
|---|---|
| `porta_aberta_madrugada` | Porta abriu entre 23:30 e 06:00: fala no alto-falante (a 80% de volume, depois volta ao anterior) e avisa no Telegram |
| `wifi_aparelho_novo` | Aparelho nunca visto no Wi-Fi: notificação no HA e no Telegram, com botões |
| `observer_wifi` | O repetidor/observer entrou ou saiu do Wi-Fi |
| `telegram_comandos`, `telegram_botoes_*` | Comandos e botões do bot |
| `telegram_internet`, `telegram_deco_offline` | Internet voltou, Deco offline |
| `telegram_impressora` | Impressão 3D terminou |
| `telegram_chuva` | Chuva chegando |
| `telegram_servidores` | Disco, temperatura, servidor fora, Traefik, Pi-hole, certificado, reinício |
| `telegram_bom_dia` | Resumo diário às 07:30 |

## Painéis

| Painel | Para quê |
|---|---|
| `painel-casa` | Painel principal com 7 abas: Casa, Sala, Escritório, Externo, Servidores, Rede, Mesh |
| `painel-tablet` | Tela única para o tablet da sala: relógio, agenda, clima, status, luzes, som |
