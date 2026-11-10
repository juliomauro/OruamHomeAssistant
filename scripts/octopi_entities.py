# octopi_entities.py v1.0 - le as entidades glances do Raspberry do OctoPrint (stdin, JSON do entity_registry/list) e gera comandos de rename/disable
import json, sys
P = "sensor.192_168_0_23_"
keep = {
    "cpu_usage": ("cpu", "CPU"),
    "cpu_thermal_1_temperature": ("temperatura", "Temperatura"),
    "memory_usage": ("memoria", "Memória"),
    "memory_free": ("memoria_livre", "Memória livre"),
    "disk_usage": ("disco", "Cartão SD"),
    "disk_free": ("disco_livre", "Cartão SD livre"),
    "swap_usage": ("swap", "Swap"),
    "cpu_load": ("load", "Carga"),
    "wlan0_rx": ("rede_download", "Download"),
    "wlan0_tx": ("rede_upload", "Upload"),
    "uptime": ("ligado_desde", "Ligado desde"),
}
ents = json.load(sys.stdin)[0]["result"]
cmds, dev = [], None
for e in ents:
    if e["platform"] != "glances" or not e["entity_id"].startswith(P):
        continue
    dev = dev or e.get("device_id")
    suf = e["entity_id"].removeprefix(P)
    if suf in keep:
        new, name = keep[suf]
        cmds.append({"type": "config/entity_registry/update", "entity_id": e["entity_id"],
                     "new_entity_id": f"sensor.octopi_{new}", "name": name, "disabled_by": None})
    else:
        cmds.append({"type": "config/entity_registry/update", "entity_id": e["entity_id"], "disabled_by": "user"})
if dev:
    cmds.append({"type": "config/device_registry/update", "device_id": dev, "name_by_user": "Octopi", "area_id": "escritorio"})
print(json.dumps(cmds, ensure_ascii=False))
