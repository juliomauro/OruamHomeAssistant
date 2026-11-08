# 2. Acesso pela API e scripts

Quase tudo deste guia foi feito por script, chamando a API do HA, e não clicando na interface. Assim dá para refazer do zero, versionar e revisar antes de aplicar.

## 2.1 Token de longa duração

1. Na interface: **Perfil > Segurança > Tokens de acesso de longa duração > Criar token**.
2. Salve o token em um arquivo protegido no servidor:

```bash
mkdir -p /DATA/AppData/.secrets/ha-tools && chmod 700 /DATA/AppData/.secrets
nano /DATA/AppData/.secrets/ha_token   # cole o token, salve
chmod 600 /DATA/AppData/.secrets/ha_token
```

Copie a pasta `scripts/` deste repositório para `/DATA/AppData/.secrets/ha-tools/`.

## 2.2 Dois jeitos de falar com o HA

### REST (`/api/...`)

Os scripts `rede_flows.py`, `rede_automacoes.py`, `telegram_automacoes.py` e `energia.py` usam REST. Eles leem a variável `HA_URL`, que tem o padrão `http://127.0.0.1:8123`:

```bash
cd /DATA/AppData/.secrets/ha-tools
HA_URL=http://192.168.0.240:8123 python3 rede_flows.py "$(cat ../ha_token)"
```

Endpoints usados:

| Endpoint | Para quê |
|---|---|
| `POST /api/config/config_entries/flow` e `/flow/{id}` | Criar integrações (config flow) sem a interface |
| `POST /api/config/automation/config/{id}` | Criar ou substituir uma automação |
| `POST /api/template` | Testar um template Jinja antes de usar |
| `POST /api/services/<dominio>/<servico>` | Chamar uma ação |

### WebSocket (`/api/websocket`)

O registro de entidades e dispositivos e os painéis só existem no WebSocket. O `ha_ws.py` recebe pelo stdin o token na primeira linha e, depois, uma lista JSON de comandos. Ele roda **dentro** do container, que já tem `aiohttp`:

```bash
{ cat ../ha_token; echo; echo '[{"type":"config/entity_registry/list"}]'; } \
  | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

O `echo` depois do `cat` é necessário: se o arquivo do token não termina com quebra de linha, o token e o JSON grudam e o HA responde `auth_invalid`.

Os geradores de painel imprimem os comandos, que depois passam pelo `ha_ws.py`:

```bash
{ cat ../ha_token; echo; python3 painel_casa.py; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

Comandos WebSocket usados:

| Comando | Para quê |
|---|---|
| `config/entity_registry/list` / `update` | Renomear (`new_entity_id`, `name`), habilitar (`disabled_by: null`) |
| `config/device_registry/update` | `name_by_user`, `area_id` |
| `lovelace/dashboards/create` | Criar painel (o `url_path` precisa ter hífen) |
| `lovelace/config/save` | Gravar a configuração do painel |
| `recorder/import_statistics` | Importar histórico (energia) |
| `trace/list` / `trace/get` | Ver por que uma automação falhou |

## 2.3 Editando o configuration.yaml

O `configuration.yaml` pertence ao root dentro do container. O fluxo seguro é:

```bash
# 1. backup
docker exec homeassistant cp /config/configuration.yaml /config/configuration.yaml.bak-assunto
# 2. gerar o novo arquivo fora do container
docker exec homeassistant cat /config/configuration.yaml > /tmp/cfg.yaml
python3 template_bloco.py /tmp/cfg.yaml chuva ../config/blocos/chuva.yaml > /tmp/cfg.novo
# 3. gravar e validar
docker exec -i homeassistant sh -c 'cat > /config/configuration.yaml' < /tmp/cfg.novo
docker exec homeassistant python3 -m homeassistant --script check_config -c /config
# 4. recarregar (template:, rest: e automações recarregam sem reiniciar)
```

Para recarregar, use **Ferramentas de desenvolvedor > YAML**, ou chame as ações `template.reload`, `rest.reload` e `automation.reload`.

O `template_bloco.py` mantém cada sensor entre `  # BLOCO <nome>` e `  # FIM <nome>` dentro de `template:`. Rodar de novo substitui o bloco em vez de duplicar.

## 2.4 Lista dos scripts

| Script | O que faz | Guia |
|---|---|---|
| `ha_ws.py` | Cliente WebSocket genérico | este |
| `template_bloco.py` | Insere ou substitui um bloco nomeado em `template:` | [7](07-sensores-template.md) |
| `agenda_template.py` | Insere o sensor `sensor.agenda_hoje` | [7](07-sensores-template.md) |
| `energia.py`, `historico_tomada.py` | Medidores de energia e custo, importação de histórico | [4](04-energia.md) |
| `boreas_entities.py` | Renomeia as entidades do Glances do boreas | [3](03-integracoes.md) |
| `rede_flows.py`, `rede_rename.py` | Ping, Speedtest e IP público | [5](05-rede.md) |
| `deco_rename.py`, `deco_nomes.py` | Padroniza as entidades do Deco e dá nome aos aparelhos por MAC | [5](05-rede.md) |
| `rede_automacoes.py` | Aviso de aparelho novo e de observer no Wi-Fi | [5](05-rede.md) |
| `lan_scan.py` | Acha roteadores e modem na LAN (título HTTP e SSDP) | [5](05-rede.md) |
| `mesh_rename.py`, `corescope_rest.py` | MeshCore e CoreScope | [6](06-meshcore.md) |
| `painel_casa.py`, `painel_tablet.py` | Painéis | [8](08-paineis.md) |
| `telegram_automacoes.py` | Todas as automações do Telegram | [9](09-telegram.md) |

Os scripts usam os nomes de entidade da minha casa. Antes de rodar, abra o script e ajuste as listas no topo, que trazem as luzes, os sensores e os MACs.
