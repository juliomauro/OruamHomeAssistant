# deco_nomes.py v1.1 - da nomes aos aparelhos do Wi-Fi (device_tracker.wifi_*) casando por MAC
# stdin: 1a linha token. Roda dentro do container do HA.
import asyncio, sys, aiohttp
NOMES = {  # MAC: (slug, nome)
    "AA-BB-CC-00-00-01": ("boreas", "boreas"),
    "AA-BB-CC-00-00-02": ("atlas", "atlas"),
    "AA-BB-CC-00-00-03": ("relogio_suite", "Relógio suíte"),
    "AA-BB-CC-00-00-04": ("som_atelier", "Som atelier"),
    "AA-BB-CC-00-00-05": ("meshcore_companion", "MeshCore companion"),
    "AA-BB-CC-00-00-06": ("icomm_28", "iComm .28"),
    "AA-BB-CC-00-00-07": ("tv", "TV"),
    "AA-BB-CC-00-00-08": ("fire_tv", "Fire TV"),
    "AA-BB-CC-00-00-09": ("tuya_6", "Tuya .6"),
    "AA-BB-CC-00-00-0A": ("tuya_8", "Tuya .8"),
    "AA-BB-CC-00-00-0B": ("tuya_11", "Tuya .11"),
    "AA-BB-CC-00-00-0C": ("tuya_4", "Tuya .4"),
    "AA-BB-CC-00-00-0D": ("esp_12", "ESP .12"),
    "AA-BB-CC-00-00-0E": ("esp_18", "ESP .18"),
    "AA-BB-CC-00-00-0F": ("camera_sala", "Câmera sala"),
}
async def main():
    tok = sys.stdin.readline().strip()
    async with aiohttp.ClientSession() as s, s.ws_connect("http://127.0.0.1:8123/api/websocket", max_msg_size=0) as ws:
        await ws.receive_json(); await ws.send_json({"type": "auth", "access_token": tok}); assert (await ws.receive_json())["type"] == "auth_ok"
        n = 0
        async def call(**c):
            nonlocal n; n += 1
            await ws.send_json({"id": n, **c})
            while True:
                m = await ws.receive_json()
                if m.get("id") == n: return m
        states = {x["entity_id"]: x for x in (await call(type="get_states"))["result"]}
        for eid, st in sorted(states.items()):
            if not eid.startswith("device_tracker.wifi_"): continue
            mac = (st["attributes"].get("mac") or "").upper()
            if mac not in NOMES: continue
            slug, nome = NOMES[mac]
            r = await call(type="config/entity_registry/update", entity_id=eid, new_entity_id=f"device_tracker.wifi_{slug}", name=nome)
            print(eid, "->", f"wifi_{slug}", nome, "OK" if r["success"] else r.get("error"))
asyncio.run(main())
