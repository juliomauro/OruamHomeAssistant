# 10. Pegadinhas

Problemas que apareceram durante a montagem, com a causa e a solução.

## Instalação

### Proxy reverso ignorado

- **Sintoma:** depois de configurar o `http:` no YAML, o Traefik continua recebendo erro 400, ou aparece o reparo "ignored after migration".
- **Causa:** no 2026.11, o `http:` migra uma única vez do YAML para `.storage/http`, e a flag `yaml_migration_done` impede uma nova leitura.
- **Solução:**
  1. Configure pela interface: **Configurações > Sistema > Rede**, com X-Forwarded-For ligado e o proxy confiável `172.17.0.0/16`.
  2. Se a interface não oferecer a opção, pare o HA e ponha `yaml_migration_done` como `false` em `/config/.storage/http`. Edite com um container temporário da mesma imagem (`docker run --rm --entrypoint python3 -v /DATA/AppData/homeassistant/config:/config ...`) e suba o HA de novo.
  3. Depois de migrado, **remova** o bloco `http:` do `configuration.yaml`.

### Backup falha

- **Sintoma:** "Addons and folders are not supported by core backup".
- **Solução:** desmarque pastas e add-ons. A instalação por container só faz backup da configuração.

### Painel não é criado

- **Sintoma:** `lovelace/dashboards/create` recusa o `url_path`.
- **Solução:** o `url_path` precisa ter hífen. Ex: `painel-casa`.

## API e scripts

| Sintoma | Causa e solução |
|---|---|
| `auth_invalid` no `ha_ws.py` | O arquivo do token não termina com quebra de linha. Use `{ cat ha_token; echo; ... }` |
| Config flow responde 400 | Você mandou um campo que o formulário não pede. Ex: `count` no Ping. Envie só os nomes que aparecem em `data_schema` |
| Config flow do DNS IP responde 400 | Resolvedor e portas vão dentro da seção `additional_options` |
| Rename falha com "entity already exists" | Duas entidades caíram no mesmo ID (Ex: dois aparelhos `wlan0`). Renomeie uma delas antes |
| `NameError` no gerador de painel | Um card foi usado antes de ser definido. Mova a definição para cima |
| `recorder/import_statistics` falha | Faltam `mean_type` e `unit_class` no metadata |

## Integrações

| Sintoma | Causa e solução |
|---|---|
| Deco: "Erro inesperado" | O host precisa do `http://`. Ex: `http://192.168.0.10` |
| Deco: "Invalid login credentials" | Use `admin` e a senha da conta dona (owner), não de uma conta manager |
| Aparelhos do Deco não aparecem | Os `device_tracker` vêm desativados. Rode o `deco_rename.py`, ou ative um por um |
| OctoPrint não carrega | Webcam configurada e sem resposta. Desligue a webcam no OctoPrint |
| Energia da tomada Tuya volta a zero | O contador da Tuya é incremental. Use a integral (Riemann) sobre a potência |
| Nomes das teclas do Smart Life não chegam | Renomeie no HA |
| Gemini: erro 402 | A conta do AI Studio está sem crédito pré-pago |
| YAML quebra com unidade `%` | Ponha aspas: `unit_of_measurement: "%"` |
| `json_attributes_path` com filtro não funciona | Use sensores separados com `selectattr` no `value_template` |

## Templates

| Sintoma | Causa e solução |
|---|---|
| Agenda fora de ordem | Algumas agendas vêm em UTC. Ordene por timestamp (`as_timestamp`), não por texto |
| "desde 48 seconds" em inglês | `relative_time` sai em inglês. Use `strftime('%H:%M')` ou monte o texto |
| "100.0%" | Use `\| float(0) \| int` |
| Sensor de latência some do card | O sensor de latência do Ping só existe depois que o host responde pela primeira vez. Não use em um card enquanto o host estiver fora |

## Painéis

| Sintoma | Causa e solução |
|---|---|
| Fonte do card-mod não muda no Mushroom 5 | Os cards usam o `ha-tile-info`. Use `--ha-tile-info-primary-font-size` e as demais variáveis, aplicadas no próprio `ha-tile-info` |
| Texto grande aparece cortado | A classe `.vertical.fixed-info-height` fixa a altura da linha. Defina `--ha-tile-info-primary-line-height` e `--ha-tile-info-primary-min-height` no `ha-tile-info` |
| Cards colados, sem borda | A view `panel` zera a borda e o arredondamento. Aplique `border-radius` e `border` com `!important` em cada card via card-mod |
| No tablet só cabem 2 colunas | A view `sections` exige pelo menos 320 px por coluna. Em tela de ~1000 pontos, use `panel` + `horizontal-stack` |
| card-mod ignorado no `horizontal-stack` | O stack não carrega o card-mod. Use `stack-card-gap` no tema para o espaço, e aplique o resto em cada card |

## Telegram

| Sintoma | Causa e solução |
|---|---|
| `httpx.ConnectError` às vezes | Sem IPv6 de saída no container. Use `continue_on_error: true`, e a próxima tentativa funciona |
| Bot não responde | O chat não está em `allowed_chat_ids`, ou o `user_id` não bate com a condição da automação |
| Botão fica "carregando" | Faltou o `telegram_bot.answer_callback_query` |
| Comando não reconhecido em grupo | O Telegram manda `/status@nome_do_bot`. Tire o sufixo com `regex_replace('@.*', '')` |

## Segurança

- Não ligue o UPnP no modem só para ter métricas.
- Câmeras IoT baratas costumam ter telnet aberto. Se não houver firmware alternativo suportado, deixe a câmera sem acesso à internet ou troque por outra. Uma rede guest isolada cortaria o RTSP para o HA.
- Não exponha o HA direto na internet. Use Tailscale ou outra VPN.
