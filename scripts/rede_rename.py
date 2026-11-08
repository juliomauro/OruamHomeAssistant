# rede_rename.py v1.0 - habilita e renomeia entidades de ping/speedtest/ip publico
# stdin: 1a linha token. Roda dentro do container do HA.
import asyncio, json, sys, aiohttp
HOSTS = {"192_168_0_1": ("modem", "Modem da operadora"), "1_1_1_1": ("cloudflare", "Cloudflare 1.1.1.1"), "8_8_8_8": ("google", "Google 8.8.8.8")}
SUF = {"round_trip_time_average": ("latencia", "Latência"), "jitter": ("jitter", "Jitter"), "packet_loss": ("perda", "Perda de pacotes")}
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
        reg = (await call(type="config/entity_registry/list"))["result"]
        byid = {e["entity_id"]: e for e in reg}
        cmds = []
        for h, (slug, nome) in HOSTS.items():
            b = byid.get(f"binary_sensor.{h}")
            if b:
                if b.get("device_id"):
                    r = await call(type="config/device_registry/update", device_id=b["device_id"], name_by_user=nome)
                    print("device", nome, r["success"])
                cmds.append(dict(entity_id=b["entity_id"], new_entity_id=f"binary_sensor.rede_{slug}", name=None))
            for suf, (s2, nm) in SUF.items():
                e = byid.get(f"sensor.{h}_{suf}")
                if e: cmds.append(dict(entity_id=e["entity_id"], new_entity_id=f"sensor.rede_{slug}_{s2}", disabled_by=None, name=None))
        for a, b in (("download", "internet_download"), ("upload", "internet_upload"), ("ping", "internet_ping")):
            if f"sensor.speedtest_{a}" in byid: cmds.append(dict(entity_id=f"sensor.speedtest_{a}", new_entity_id=f"sensor.{b}"))
        if "sensor.myip" in byid: cmds.append(dict(entity_id="sensor.myip", new_entity_id="sensor.internet_ip_publico", name="IP público"))
        for c in cmds:
            r = await call(type="config/entity_registry/update", **c)
            print(c["entity_id"], "->", c["new_entity_id"], r["success"], r.get("error") or "")
asyncio.run(main())
