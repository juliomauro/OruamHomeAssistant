# 5. Network: internet and Wi-Fi mesh

## 5.1 ISP modem

The ISP modem (192.168.0.1) has no SNMP. It has UPnP, but **I decided not to turn it on**: with UPnP, any IoT device in the house can open ports on the router by itself.

So the internet is monitored "from the outside", with built-in integrations.

## 5.2 Internet: ping, speedtest and public IP

`rede_flows.py` creates the integrations through config flows. It only sends the fields the form asks for, and skips the ones that already exist:

| Integration | Target | Purpose |
|---|---|---|
| Ping | 192.168.0.1 | Does the modem answer? |
| Ping | 1.1.1.1 and 8.8.8.8 | Does the internet answer? |
| Ping | 192.168.0.27 | Is the MeshCore observer on the Wi-Fi? |
| Speedtest.net | | Download, upload, ping |
| DNS IP | `myip.opendns.com` through the OpenDNS resolver | Public IP |

```bash
HA_URL=http://192.168.0.240:8123 python3 rede_flows.py "$(cat ../ha_token)"
{ cat ../ha_token; echo; } | docker exec -i homeassistant python3 -c "$(cat rede_rename.py)"
```

`rede_rename.py` enables the latency, jitter and loss sensors, which come disabled, and sets these names (`rede` = network, `latencia` = latency, `perda` = loss, `ip_publico` = public IP):

- `binary_sensor.rede_modem`, `rede_cloudflare`, `rede_google`, `rede_observer`
- `sensor.rede_<x>_latencia`, `_jitter`, `_perda`
- `sensor.internet_download`, `internet_upload`, `internet_ping`
- `sensor.internet_ip_publico`

"Internet ok" on the dashboard and on Telegram means Cloudflare **or** Google answering.

## 5.3 TP-Link Deco (Wi-Fi mesh)

I use the community integration [`amosyuen/ha-tplink-deco`](https://github.com/amosyuen/ha-tplink-deco), installed manually in `/config/custom_components/tplink_deco`, followed by an HA restart.

To find the IPs of the Decos on the network, run `python3 lan_scan.py`. It lists the HTTP title of each IP and the SSDP answers.

Configuration (also follow the [integration README](https://github.com/amosyuen/ha-tplink-deco#configuration-important-please-read)):

| Field | Value |
|---|---|
| Host | `http://192.168.0.10`, **with** the `http://`. Without it you get "Unexpected error" |
| Username | `admin` |
| Password | the password of the Deco **owner** account. A "manager" account gives "Invalid login credentials" |

After setting it up:

1. Put each Deco in the right area: Deco Sala (main, living room) and Deco Office (wired backhaul).
2. Run `deco_rename.py`:

```bash
{ cat ../ha_token; echo; } | docker exec -i homeassistant python3 -c "$(cat deco_rename.py)"
```

It standardizes the names and enables the entities that come disabled:

- `sensor.deco_sala_*` and `sensor.deco_office_*`: connected clients, CPU, memory, traffic, backhaul type;
- `binary_sensor.deco_sala_online` and `deco_office_online`;
- `device_tracker.wifi_<device>`: one per device, with the attributes `mac`, `ip`, `deco_device`, `connection_type` (`band2_4`, `band5`, `wired`), `down_kilobytes_per_s` and `up_kilobytes_per_s`.

### Naming the devices

The Deco uses the hostname, which is often `wlan0` or `ESP_xxxx`. `deco_nomes.py` matches by **MAC** and renames. To use it:

1. Fill the `NOMES` dictionary at the top, in the format `"AA-BB-CC-DD-EE-FF": ("slug", "Name")`.
2. Run:

```bash
{ cat ../ha_token; echo; } | docker exec -i homeassistant python3 -c "$(cat deco_nomes.py)"
```

Tip: the MAC prefix (OUI) helps to identify the vendor. For example, Tuya or Espressif (ESP).

### DHCP reservations

Compare the modem's reservation table with its lease table:

- reservations for random MACs (phones with "private MAC") are useless;
- a device with a static IP configured on itself does not need a reservation;
- a device with a reservation and no lease is not connected. That is how I found out the MeshCore observer had dropped off the Wi-Fi.

## 5.4 Network automations

`rede_automacoes.py` creates two automations. Later, `telegram_automacoes.py` replaces the first one with the Telegram version:

| Automation | Trigger |
|---|---|
| `wifi_aparelho_novo` (new Wi-Fi device) | Event `entity_registry_updated` with `action: create` and an `entity_id` matching `device_tracker\.(sala\|office)_deco_` |
| `observer_wifi` | `binary_sensor.rede_observer` stays off for 2 h, or comes back after being off for 2 h or more |

The Deco integration **does not fire a new client event**. But it creates a `device_tracker` only once per never seen MAC, and that creation is the "new device" signal. The new tracker starts disabled.

The integration **has no service to block a device**, only `reboot_deco`. Blocking is done in the Deco app.
