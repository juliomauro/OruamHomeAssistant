# 1. Installation

## 1.1 Container

I installed it from the ZimaOS app store (the "Home Assistant" app by BigBearTechWorld). The equivalent compose file, which also works with plain Docker, is in [`config/compose.yaml`](../config/compose.yaml):

```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    network_mode: host          # needed for discovery (Cast, mDNS, SSDP) and Bluetooth
    restart: unless-stopped
    cap_add: [NET_ADMIN, NET_RAW] # ping and network scanner
    environment:
      - TZ=America/Sao_Paulo
    volumes:
      - /DATA/AppData/homeassistant/config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
      - /media/4tb:/media/4tb:ro  # optional: media disk, read only
```

Important points:

- **`network_mode: host`** is required for Cast, device discovery and the ping integrations.
- The port is **8123**.
- Files in `/config` belong to root. To edit them, use `docker exec homeassistant ...` or the interface.
- On ZimaOS, volume changes are made in the app interface. If you edit the compose file by hand, Zima overwrites it.

```bash
docker compose -f config/compose.yaml up -d
docker logs -f homeassistant   # wait for "Home Assistant initialized"
```

## 1.2 First access

1. Open `http://SERVER_IP:8123`.
2. Create the owner user.
3. Set the home location, which is used by the weather (`weather.casa`) and by sunrise and sunset.
4. Choose the unit system (metric) and the currency.

## 1.3 Reverse proxy with Traefik (optional)

I use Traefik with a Let's Encrypt wildcard certificate for `*.example.com`, reachable only on the LAN and through Tailscale. The route lives in the Traefik dynamic file:

```yaml
http:
  routers:
    ha:
      rule: Host(`ha.example.com`)
      entryPoints: [websecure]
      service: ha
      tls: {}
  services:
    ha:
      loadBalancer:
        servers:
          - url: http://192.168.0.240:8123
```

HA rejects connections that come through a proxy until you allow the proxy. **In 2026.11 this setting moved**:

- It now lives in `.storage/http` and is edited in the interface: **Settings > System > Network**, with "Use X-Forwarded-For" on and the trusted proxy `172.17.0.0/16`, which is the Docker network of Traefik.
- The `http:` block in `configuration.yaml` is read only once, during the migration. After that it must **leave** the file, or a repair "ignored after migration" shows up.

If the migration already ran with wrong values, see [Gotchas](10-gotchas.md#reverse-proxy-ignored).

## 1.4 Marketplace (community cards)

In 2026.11 HACS is built in, under the name **Marketplace**. Do not install HACS separately.

I installed these cards, which the dashboards use:

| Card | Use |
|---|---|
| Mushroom (v5) | Template, entity and media cards |
| mini-graph-card | Compact graphs |
| card-mod | CSS tweaks (large fonts on the tablet) |

Each install asks you to accept it in the interface.

Integrations that are not in the Marketplace (for example `tplink_deco`) go manually into `/config/custom_components/<name>`, followed by an HA restart.

## 1.5 Backup

In **Settings > System > Backups**:

- daily at 04:30, keeping 7 copies;
- targets: local + Google Drive (needs the Google Drive integration, see [Integrations](03-integrations.md#google));
- encryption on.

**Store the encryption key in your password manager.** Without it the backup does not restore.

On a container install, the backup does **not** accept extra folders or add-ons. If the interface wizard selects these options, the backup fails with "Addons and folders are not supported by core backup".

Also note: the backup wizard overwrites targets, schedule and retention. After you use it, check that the options are still what you want.
