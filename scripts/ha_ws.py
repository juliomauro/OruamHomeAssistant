# ha_ws.py v1.1 - roda comandos no WebSocket do Home Assistant
# stdin: 1a linha = token; resto = JSON com lista de comandos (sem "id")
# Ex: { cat token; echo '[{"type":"config/entity_registry/list"}]'; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
import asyncio, json, sys
import aiohttp

async def main():
    token = sys.stdin.readline().strip()
    cmds = json.loads(sys.stdin.read() or "[]")
    async with aiohttp.ClientSession() as s:
        async with s.ws_connect("http://127.0.0.1:8123/api/websocket", max_msg_size=0) as ws:
            await ws.receive_json()
            await ws.send_json({"type": "auth", "access_token": token})
            r = await ws.receive_json()
            if r.get("type") != "auth_ok":
                print(json.dumps({"auth": r})); return
            out = []
            for i, c in enumerate(cmds, 1):
                await ws.send_json({"id": i, **c})
                while True:
                    m = await ws.receive_json()
                    if m.get("id") == i and m.get("type") == "result":
                        out.append({"cmd": c.get("type"), "success": m.get("success"),
                                    "result": m.get("result"), "error": m.get("error")})
                        break
            print(json.dumps(out))

asyncio.run(main())
