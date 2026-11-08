# rede_flows.py v1.3 - cria integracoes nativas de rede (ping, speedtest, ip publico) via config flow
# uso: python3 rede_flows.py <token>
import os, json, sys, time, urllib.request
T = sys.argv[1]; B = os.environ.get("HA_URL", "http://127.0.0.1:8123") + "/api"
def req(m, p, body=None):
    r = urllib.request.Request(B + p, method=m, data=json.dumps(body).encode() if body is not None else None,
                               headers={"Authorization": "Bearer " + T, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as x: return json.loads(x.read() or "null")
for _ in range(30):
    if req("GET", "/config")["state"] == "RUNNING": break
    time.sleep(5)
print("HA", req("GET", "/config")["state"])
ents = req("GET", "/config/config_entries/entry")
have = {(e["domain"], e["title"]) for e in ents}
print("ja existe:", sorted(t for d, t in have if d in ("ping", "speedtestdotnet", "dnsip", "tplink_deco")))
def flow(handler, steps, title):
    if any(d == handler and (t == title or handler == "speedtestdotnet") for d, t in have):
        print("pula", handler, title); return
    f = req("POST", "/config/config_entries/flow", {"handler": handler, "show_advanced_options": False})
    print(handler, "step", f.get("step_id"), f.get("type"), [s["name"] for s in f.get("data_schema", [])])
    for s in steps:
        if f.get("type") != "form": break
        campos = [x["name"] for x in f.get("data_schema", [])]
        f = req("POST", "/config/config_entries/flow/" + f["flow_id"], {k: v for k, v in s.items() if k in campos})
        print("  ->", f.get("type"), f.get("title") or f.get("step_id"), f.get("errors") or "", f.get("reason") or "")
flow("ping", [{"host": "192.168.0.1", "count": 5}], "192.168.0.1")
flow("ping", [{"host": "1.1.1.1", "count": 5}], "1.1.1.1")
flow("ping", [{"host": "8.8.8.8", "count": 5}], "8.8.8.8")
flow("ping", [{"host": "192.168.0.27"}], "192.168.0.27")
flow("speedtestdotnet", [{}], "SpeedTest")
flow("dnsip", [{"hostname": "myip.opendns.com", "additional_options": {"resolver": "208.67.222.222", "resolver_ipv6": "2620:119:53::53", "port": 53, "port_ipv6": 53}}], "myip.opendns.com")
