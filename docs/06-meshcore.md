# 6. MeshCore

[MeshCore](https://meshcore.co.uk) is a LoRa mesh messaging network. The house has:

- a **companion** (the radio HA uses to talk to the mesh), in my case a V3 board with the Wi-Fi companion firmware, at 192.168.0.40:5000;
- a **repeater**, REP-CASA-4387, which also runs the **observer** firmware: it sends the packets it hears to the community CoreScope over MQTT.

## 6.1 meshcore-ha integration

1. In the **Marketplace**, add the custom repository `https://github.com/meshcore-dev/meshcore-ha` (type Integration) and download **MeshCore**.
2. Restart HA.
3. Add the **MeshCore** integration with a **TCP** connection, on the companion's host and port.
4. In **Contact Discovery Mode**, use **Data only**. On a large mesh, the default mode creates hundreds of entities.
5. To add the repeater as a tracked node, use its admin password, typed in the interface. Telemetry is read every 3600 s, to save airtime.

`mesh_rename.py` generates the commands that shorten the IDs: `sensor.mesh_*` for the companion and `sensor.repetidor_*` (repeater) for the repeater. The prefixes (`c0ffee`, `43879f79cd`) come from my keys: adjust them to yours.

Do not rename the `select.meshcore_*` and `text.meshcore_*` entities. The `meshcore.send_ui_message` action depends on them.

## 6.2 Received messages

Every received message fires the `meshcore_message` event. A template sensor keeps the last 15 messages in the `mensagens` attribute (see the last item of [`config/configuration-template.yaml`](../config/configuration-template.yaml)). The dashboard shows that attribute.

## 6.3 CoreScope (public community data)

CoreScope is a community website that shows the mesh nodes, who relayed what and the observers. In my case I use `corescope.example.org`. Its API is public, and the documentation is at `/api/spec`. Send your own `User-Agent`.

`corescope_rest.py` generates the `rest:` items for a list of nodes (the `NOS` dictionary: slug, name, public key):

```bash
python3 corescope_rest.py > corescope.yaml   # paste inside rest:
```

| Sensor | Endpoint | Interval |
|---|---|---|
| `sensor.corescope_<slug>` (packets relayed in 24 h + node attributes) | `/api/nodes/<pk>` | 1 h |
| `_disponibilidade` (availability), `_relogio` (clock) | `/api/nodes/<pk>/analytics?days=7` | 3 h |
| `_vizinhos` (neighbors), `_melhor_vizinho` (best neighbor) | `/api/nodes/<pk>/neighbors` | 1 h |
| `sensor.corescope_canal_public` | `/api/channels/Public/messages?limit=20` | 2 min |
| `sensor.corescope_meu_observer*` (packets per hour, last packet, firmware) | `/api/observers` | 10 min |

The result generated for my case is in [`config/configuration-corescope.yaml`](../config/configuration-corescope.yaml).

Watch out:

- A `%` unit in YAML needs quotes (`"%"`). Without quotes the configuration breaks.
- `json_attributes_path` with a filter (`$[?(...)]`) does **not work** in HA. To pick one item from a list, create separate sensors with `selectattr` in the `value_template`.
- The `analytics` answer for a busy node is about 1.7 MB. Do not lower the interval.

## 6.4 Observer troubleshooting

The "Observer upload" card turns green when `sensor.corescope_meu_observer_ultimo_pacote` is less than 10 min old.

If the observer connects (heartbeat) but uploads no packets, check in this order:

1. **Is it on the Wi-Fi?** Look at `binary_sensor.rede_observer` and the Deco client list. The ESP32 only connects to 2.4 GHz.
2. **Is MQTT configured?** Server, IATA code and packet upload turned on.
3. **Antenna and cable:** many `recv_errors` and few packets per day point to an RF problem.
4. **Firmware:** update to the **observer** build. The "stock" update that HA offers replaces the firmware and removes the observer.
