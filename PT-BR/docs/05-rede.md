# 5. Rede: internet e Wi-Fi mesh

## 5.1 Modem da operadora

O modem da operadora (192.168.0.1) não tem SNMP. Ele tem UPnP, mas **decidi não ligar**: com UPnP, qualquer aparelho IoT da casa pode abrir portas no roteador sozinho.

Então o monitoramento da internet é feito "por fora", com integrações nativas.

## 5.2 Internet: ping, speedtest e IP público

O `rede_flows.py` cria as integrações por config flow. Ele só envia os campos que o formulário pede, e pula as que já existem:

| Integração | Alvo | Uso |
|---|---|---|
| Ping | 192.168.0.1 | O modem responde? |
| Ping | 1.1.1.1 e 8.8.8.8 | A internet responde? |
| Ping | 192.168.0.27 | O observer MeshCore está no Wi-Fi? |
| Speedtest.net | | Download, upload, ping |
| DNS IP | `myip.opendns.com` via resolvedor OpenDNS | IP público |

```bash
HA_URL=http://192.168.0.240:8123 python3 rede_flows.py "$(cat ../ha_token)"
{ cat ../ha_token; echo; } | docker exec -i homeassistant python3 -c "$(cat rede_rename.py)"
```

O `rede_rename.py` habilita os sensores de latência, jitter e perda, que vêm desligados, e deixa os nomes assim:

- `binary_sensor.rede_modem`, `rede_cloudflare`, `rede_google`, `rede_observer`
- `sensor.rede_<x>_latencia`, `_jitter`, `_perda`
- `sensor.internet_download`, `internet_upload`, `internet_ping`
- `sensor.internet_ip_publico`

"Internet ok" no painel e no Telegram quer dizer Cloudflare **ou** Google respondendo.

## 5.3 TP-Link Deco (Wi-Fi mesh)

Uso a integração da comunidade [`amosyuen/ha-tplink-deco`](https://github.com/amosyuen/ha-tplink-deco), instalada manualmente em `/config/custom_components/tplink_deco`, seguida de um reinício do HA.

Para achar os IPs dos Decos na rede, rode `python3 lan_scan.py`. Ele lista o título HTTP de cada IP e as respostas SSDP.

Configuração (siga também o [README da integração](https://github.com/amosyuen/ha-tplink-deco#configuration-important-please-read)):

| Campo | Valor |
|---|---|
| Host | `http://192.168.0.10`, **com** o `http://`. Sem ele aparece "Erro inesperado" |
| Usuário | `admin` |
| Senha | a senha da conta **dona** (owner) do Deco. Conta "manager" dá "Invalid login credentials" |

Depois de configurar:

1. Coloque cada Deco na área certa: Deco Sala (principal) e Deco Office (backhaul por cabo).
2. Rode o `deco_rename.py`:

```bash
{ cat ../ha_token; echo; } | docker exec -i homeassistant python3 -c "$(cat deco_rename.py)"
```

Ele padroniza os nomes e liga as entidades que vêm desativadas:

- `sensor.deco_sala_*` e `sensor.deco_office_*`: clientes conectados, CPU, memória, tráfego, tipo de backhaul;
- `binary_sensor.deco_sala_online` e `deco_office_online`;
- `device_tracker.wifi_<aparelho>`: um por aparelho, com os atributos `mac`, `ip`, `deco_device`, `connection_type` (`band2_4`, `band5`, `wired`), `down_kilobytes_per_s` e `up_kilobytes_per_s`.

### Dando nome aos aparelhos

O Deco usa o hostname, que muitas vezes é `wlan0` ou `ESP_xxxx`. O `deco_nomes.py` casa pelo **MAC** e renomeia. Para isso:

1. Preencha o dicionário `NOMES` no topo, no formato `"AA-BB-CC-DD-EE-FF": ("slug", "Nome")`.
2. Rode:

```bash
{ cat ../ha_token; echo; } | docker exec -i homeassistant python3 -c "$(cat deco_nomes.py)"
```

Dica: o prefixo do MAC (OUI) ajuda a identificar o fabricante. Ex: Tuya ou Espressif (ESP).

### Reservas DHCP

Compare a tabela de reservas do modem com a de concessões (leases):

- reservas de MAC aleatório (celulares com "MAC privado") não servem para nada;
- aparelho com IP fixo configurado nele mesmo não precisa de reserva;
- aparelho com reserva e sem concessão não está conectado. Foi assim que descobri que o observer do MeshCore tinha saído do Wi-Fi.

## 5.4 Automações de rede

O `rede_automacoes.py` cria duas automações. Depois o `telegram_automacoes.py` substitui a primeira pela versão com Telegram:

| Automação | Gatilho |
|---|---|
| `wifi_aparelho_novo` | Evento `entity_registry_updated` com `action: create` e `entity_id` casando `device_tracker\.(sala\|office)_deco_` |
| `observer_wifi` | `binary_sensor.rede_observer` fica desligado por 2 h, ou volta depois de 2 h ou mais desligado |

A integração do Deco **não dispara evento de cliente novo**. Mas ela cria um `device_tracker` uma única vez por MAC nunca visto, e essa criação é o sinal de "aparelho novo". O tracker novo nasce desativado.

A integração **não tem serviço de bloquear aparelho**, só `reboot_deco`. O bloqueio é feito pelo app Deco.
