# 6. MeshCore

[MeshCore](https://meshcore.co.uk) é uma rede mesh LoRa de mensagens. A casa tem:

- um **companion** (rádio que o HA usa para falar com o mesh), que no meu caso é uma placa V3 com firmware companion Wi-Fi, em 192.168.0.40:5000;
- um **repetidor**, o REP-CASA-4387, que também roda o firmware **observer**: ele envia os pacotes que ouve para o CoreScope da comunidade via MQTT.

## 6.1 Integração meshcore-ha

1. No **Marketplace**, adicione o repositório personalizado `https://github.com/meshcore-dev/meshcore-ha` (tipo Integração) e baixe **MeshCore**.
2. Reinicie o HA.
3. Adicione a integração **MeshCore** com conexão **TCP**, no host e na porta do companion.
4. Em **Contact Discovery Mode**, use **Data only**. Em mesh grande, o modo padrão cria centenas de entidades.
5. Para adicionar o repetidor como nó acompanhado, use a senha de admin dele, digitada na interface. A telemetria é lida a cada 3600 s, para economizar airtime.

O `mesh_rename.py` gera os comandos que encurtam os IDs: `sensor.mesh_*` para o companion e `sensor.repetidor_*` para o repetidor. Os prefixos (`c0ffee`, `43879f79cd`) são os das minhas chaves: ajuste os seus.

Não renomeie as entidades `select.meshcore_*` e `text.meshcore_*`. A ação `meshcore.send_ui_message` depende delas.

## 6.2 Mensagens recebidas

Toda mensagem recebida dispara o evento `meshcore_message`. Um sensor de template guarda as últimas 15 mensagens no atributo `mensagens` (ver o último item de [`config/configuration-template.yaml`](../../config/configuration-template.yaml)). O painel mostra esse atributo.

## 6.3 CoreScope (dados públicos da comunidade)

O CoreScope é um site da comunidade que mostra os nós do mesh, quem repetiu o quê e os observers. No meu caso uso o `corescope.example.org`. A API dele é pública; a documentação fica em `/api/spec`. Mande um `User-Agent` próprio.

O `corescope_rest.py` gera os itens `rest:` para uma lista de nós (dicionário `NOS`: slug, nome, chave pública):

```bash
python3 corescope_rest.py > corescope.yaml   # cole dentro de rest:
```

| Sensor | Endpoint | Intervalo |
|---|---|---|
| `sensor.corescope_<slug>` (pacotes repetidos 24 h + atributos do nó) | `/api/nodes/<pk>` | 1 h |
| `_disponibilidade`, `_relogio` | `/api/nodes/<pk>/analytics?days=7` | 3 h |
| `_vizinhos`, `_melhor_vizinho` | `/api/nodes/<pk>/neighbors` | 1 h |
| `sensor.corescope_canal_public` | `/api/channels/Public/messages?limit=20` | 2 min |
| `sensor.corescope_meu_observer*` (pacotes por hora, último pacote, firmware) | `/api/observers` | 10 min |

O resultado gerado no meu caso está em [`config/configuration-corescope.yaml`](../../config/configuration-corescope.yaml).

Cuidados:

- Uma unidade `%` no YAML precisa de aspas (`"%"`). Sem aspas a configuração quebra.
- O `json_attributes_path` com filtro (`$[?(...)]`) **não funciona** no HA. Para pegar um item de uma lista, crie sensores separados com `selectattr` no `value_template`.
- A resposta de `analytics` de um nó movimentado tem cerca de 1,7 MB. Não diminua o intervalo.

## 6.4 Diagnóstico do observer

O card "Observer upload" fica verde quando `sensor.corescope_meu_observer_ultimo_pacote` tem menos de 10 min.

Se o observer conecta (heartbeat) mas não sobe pacotes, confira nesta ordem:

1. **Ele está no Wi-Fi?** Veja `binary_sensor.rede_observer` e a lista do Deco. O ESP32 só conecta em 2,4 GHz.
2. **O MQTT está configurado?** Servidor, IATA e envio de pacotes ligado.
3. **Antena e cabo:** muitos `recv_errors` e poucos pacotes por dia indicam problema de RF.
4. **Firmware:** atualize para o build **observer**. O update "stock" que o HA oferece troca o firmware e tira o observer.
