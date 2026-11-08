# deco_nomes.py v1.1 - da nomes aos aparelhos do Wi-Fi (device_tracker.wifi_*) casando por MAC
# stdin: 1a linha token. Roda dentro do container do HA.
import asyncio, sys, aiohttp
NOMES = {  # MAC (como o Deco mostra, com hifen): (slug, nome)
    "AA-BB-CC-00-00-01": ("boreas", "boreas"),
    "AA-BB-CC-00-00-02": ("tv", "TV"),
    "AA-BB-CC-00-00-03": ("camera_sala", "Câmera sala"),
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
