# deco_rename.py v1.0 - padroniza ids do tplink_deco (deco_sala_*, deco_office_*, wifi_*) e habilita sensores uteis
# stdin: 1a linha token. Roda dentro do container do HA.
import asyncio, re, sys, aiohttp
PREF = [("escritorio_sala_deco_", "deco_sala_"), ("sala_de_estar_office_deco_", "deco_office_"),
        ("sala_deco_", "deco_sala_"), ("office_deco_", "deco_office_")]
LIGAR = ("cpu_usage", "memory_usage", "ip_address", "backhaul_type", "main_wifi")
def novo(eid):
    dom, obj = eid.split(".", 1)
    if dom == "device_tracker":
        if obj in ("sala_deco", "office_deco"): return f"{dom}.deco_{obj.split('_')[0]}"
        return f"{dom}.wifi_" + re.sub(r"^(sala|office)_deco_", "", obj)
    for a, b in PREF:
        if obj.startswith(a):
            r = b + obj[len(a):]
            r = r.replace("deco_sala_sala_", "deco_sala_").replace("deco_office_office_", "deco_office_").replace("_deco_deco_", "_deco_")
            r = re.sub(r"^(deco_(?:sala|office))_deco_(online)$", r"\1_\2", r)
            return f"{dom}.{r}"
    return eid
async def main():
    tok = sys.stdin.readline().strip()
    async with aiohttp.ClientSession() as s, s.ws_connect("http://127.0.0.1:8123/api/websocket") as ws:
        await ws.receive_json(); await ws.send_json({"type": "auth", "access_token": tok}); assert (await ws.receive_json())["type"] == "auth_ok"
        n = 0
        async def call(**c):
            nonlocal n; n += 1
            await ws.send_json({"id": n, **c})
            while True:
                m = await ws.receive_json()
                if m.get("id") == n: return m
        reg = [e for e in (await call(type="config/entity_registry/list"))["result"] if e["platform"] == "tplink_deco"]
        for e in reg:
            eid = e["entity_id"]; c = {}
            nid = novo(eid)
            if nid != eid: c["new_entity_id"] = nid
            if e.get("disabled_by") == "integration" and (eid.startswith("device_tracker.") or eid.endswith(LIGAR)):
                c["disabled_by"] = None
            if not c: continue
            r = await call(type="config/entity_registry/update", entity_id=eid, **c)
            print(eid, "->", c.get("new_entity_id", "="), "LIGADO" if "disabled_by" in c else "", "OK" if r["success"] else r.get("error"))
asyncio.run(main())
