# 3. Integrações

Todas foram adicionadas em **Configurações > Dispositivos e serviços > Adicionar integração**, exceto as marcadas como YAML.

## Tuya (Smart Life)

Uso a integração Tuya oficial, pela nuvem: no app Smart Life, vá em **Eu > Configurações > Conta** e leia o QR code que o HA mostra.

O que entrou:

- interruptores da sala, escritório e quintal (`switch.*`);
- sensor da porta (`binary_sensor.entrada_porta_de_entrada_porta`);
- PIR da escada;
- termômetro da cozinha;
- tomada com medição de energia;
- robô aspirador (`vacuum.sala_de_estar_rubi`);
- cenas de IR (`scene.*`).

Dicas:

- Os nomes de cada tecla dos interruptores múltiplos no app **não** chegam no HA. Renomeie no HA.
- Teclas que não estão ligadas em nada podem ser desativadas na entidade.
- Plano futuro: migrar para o Tuya Local, que funciona sem nuvem e precisa das chaves locais de uma conta dev Tuya.

## Google Cast

A integração descobre sozinha os alto-falantes e telas: Som atelier, Relógio suíte (relógio smart) e o grupo "Toda casa". O TTS usado nas automações é o `tts.google_translate_en_com` com `language: pt-br`.

## OctoPrint (impressora 3D)

- Host: 192.168.0.23.
- **Desligue a webcam no OctoPrint** se ela não existir. Com a webcam ligada e sem resposta, a integração inteira falha.
- Entidades usadas: `binary_sensor.escritorio_octoprint_printing`, `sensor.escritorio_octoprint_job_percentage`, `_estimated_finish_time`, `_current_file`, `_current_state`.

## Servidores

| Servidor | Integração | Entidades |
|---|---|---|
| atlas (o próprio HA) | System Monitor | `sensor.atlas_*` (CPU, memória, disco, `atlas_4tb`, temperatura, `atlas_ligado_desde`) |
| boreas | Glances | `sensor.boreas_*` |

No boreas, o Glances roda em modo web, ouvindo só no IP da LAN:

```bash
glances -w --disable-webui -B 192.168.0.241 -p 61208
```

A integração cria dezenas de sensores com nomes como `sensor.192_168_0_241_cpu_usage`. O `boreas_entities.py` gera os comandos para renomear os úteis para `sensor.boreas_cpu`, `boreas_temperatura`, `boreas_disco` etc. e desativar o resto:

```bash
{ cat ../ha_token; echo; echo '[{"type":"config/entity_registry/list"}]'; } \
  | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)" > lista.json
python3 boreas_entities.py < lista.json > cmds.json
{ cat ../ha_token; echo; cat cmds.json; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

## Pi-hole, Transmission, Plex

- **Pi-hole:** `sensor.pihole_*` e `switch.pihole`, que liga e desliga o bloqueio.
- **Transmission:** `sensor.transmission_*` e `switch.transmission`.
- **Plex:** a integração pede login no plex.tv. Ela cria `sensor.plex_assistindo` (quantas pessoas estão assistindo agora) e um sensor por biblioteca.

## Google

As três integrações usam **o mesmo cliente OAuth**:

1. No Google Cloud Console, crie um projeto e ative as APIs **Google Calendar**, **Google Drive** e **Generative Language**.
2. Crie uma credencial **OAuth client ID** do tipo **Web application**, com o redirect URI `https://my.home-assistant.io/redirect/oauth`.
3. No HA, em **Configurações > Dispositivos e serviços > ⋮ > Credenciais de aplicativo**, cadastre o client ID e o secret.
4. Adicione **Google Calendar** e **Google Drive** e faça o login.

| Integração | Uso |
|---|---|
| Google Calendar | Um `calendar.*` por agenda. Uso pessoal, família, aniversários, feriados, escola e F1 |
| Google Drive | Destino do backup automático |
| Google Gemini (Generative AI) | Pipeline do Assist em pt-BR. Exige crédito pré-pago no AI Studio, senão dá erro 402 |

## Câmera

A câmera da sala entra como **Generic Camera**, com o stream RTSP `rtsp://192.168.0.51:554/av_stream/ch0` (câmera IP genérica).

O snapshot, que é a foto parada, ainda falha com erro 500 por causa de keyframes espaçados no stream. O vídeo ao vivo funciona.

## Traefik e Stacklog (YAML, `rest:`)

Esses dois serviços não têm integração própria, então leio as APIs deles com `rest:` no `configuration.yaml`. O trecho completo está em [`config/configuration-rest.yaml`](../../config/configuration-rest.yaml).

| Sensor | Fonte |
|---|---|
| `binary_sensor.traefik_online`, `sensor.traefik_rotas/servicos/problemas` | `https://traefik.example.com/api/overview`, a cada 60 s |
| `sensor.stacklog_abertas`, `_concluidas_hoje`, `_ultima_concluida`, `_concluidas_7_dias`, `_observacoes`, `_projetos_ativos` | API do Stacklog, a cada 5 min, só leitura |

O certificado é acompanhado pela integração **Certificate Expiry** (`cert_expiry`), apontando para `ha.example.com:443`, que cria `sensor.traefik_certificado`.

Depois de adicionar ou mudar blocos `rest:`, rode a ação `rest.reload`. Não precisa reiniciar.
