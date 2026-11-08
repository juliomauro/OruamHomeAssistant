# boreas_entities.py v1.0 - le a lista de entidades glances (stdin, JSON do entity_registry/list) e gera comandos de rename/disable
import json, sys
P = "sensor.192_168_0_241_"
keep = {
    "cpu_usage": ("cpu", "CPU"),
    "package_id_0_temperature": ("temperatura", "Temperatura"),
    "memory_usage": ("memoria", "Memória"),
    "memory_free": ("memoria_livre", "Memória livre"),
    "etc_hostname_disk_usage": ("disco", "Disco"),
    "etc_hostname_disk_free": ("disco_livre", "Disco livre"),
    "cpu_load": ("load", "Carga"),
    "enp2s0_rx": ("rede_download", "Download"),
    "enp2s0_tx": ("rede_upload", "Upload"),
    "tailscale0_rx": ("tailscale_download", "Tailscale download"),
    "tailscale0_tx": ("tailscale_upload", "Tailscale upload"),
    "containers_active": ("containers", "Containers ativos"),
    "uptime": ("ligado_desde", "Ligado desde"),
}
ents = json.load(sys.stdin)[0]["result"]
cmds, dev = [], None
for e in ents:
    if e["platform"] != "glances":
        continue
    dev = dev or e.get("device_id")
    suf = e["entity_id"].removeprefix(P)
    if suf in keep:
        new, name = keep[suf]
        cmds.append({"type": "config/entity_registry/update", "entity_id": e["entity_id"],
                     "new_entity_id": f"sensor.boreas_{new}", "name": name, "disabled_by": None})
    else:
        cmds.append({"type": "config/entity_registry/update", "entity_id": e["entity_id"], "disabled_by": "user"})
if dev:
    cmds.append({"type": "config/device_registry/update", "device_id": dev, "name_by_user": "Boreas"})
print(json.dumps(cmds, ensure_ascii=False))
