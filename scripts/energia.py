# energia.py v1.0 - cria medidores dia/mes e custo em R$ da tomada do escritorio (roda no atlas, ao lado do ha_token)
import os, json, urllib.request

T = open("ha_token").read().strip()
BASE = os.environ.get("HA_URL", "http://127.0.0.1:8123") + "/api"
SRC = "sensor.escritorio_mesa_energia_total"

def api(path, data=None, method=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": "Bearer " + T, "Content-Type": "application/json"},
                                 method=method)
    try:
        return json.loads(urllib.request.urlopen(req).read().decode() or "null")
    except urllib.error.HTTPError as e:
        return {"http_error": e.code, "body": e.read().decode()[:300]}

def flow(handler, *steps):
    r = api("/config/config_entries/flow", {"handler": handler})
    for s in steps:
        if r.get("type") not in ("form", "menu"):
            break
        r = api("/config/config_entries/flow/" + r["flow_id"], s)
    if r.get("type") != "create_entry":
        if r.get("flow_id"):
            api("/config/config_entries/flow/" + r["flow_id"], method="DELETE")
        return "ERRO: " + json.dumps(r)[:400]
    return "ok: " + r["title"]

existing = {e["title"] for e in api("/config/config_entries/entry")}

for name, cycle in (("Setup escritório hoje", "daily"), ("Setup escritório mês", "monthly")):
    if name in existing:
        print("ja existe:", name); continue
    print(flow("utility_meter", {"name": name, "source": SRC, "cycle": cycle, "offset": 0, "tariffs": [],
                                 "net_consumption": False, "delta_values": False, "periodically_resetting": True,
                                 "always_available": True}))

for name, meter in (("Custo setup hoje", "sensor.setup_escritorio_hoje"), ("Custo setup mês", "sensor.setup_escritorio_mes")):
    if name in existing:
        print("ja existe:", name); continue
    state = "{{ (states('%s') | float(0) * states('input_number.preco_do_kwh') | float(0)) | round(2) }}" % meter
    print(flow("template", {"next_step_id": "sensor"},
               {"name": name, "state": state, "unit_of_measurement": "BRL",
                "device_class": "monetary", "state_class": "total"}))
