# lan_scan.py v1.0 - acha Decos e o modem na LAN (titulo HTTP + SSDP)
import socket, re, urllib.request, ssl, concurrent.futures as cf, time
ctx = ssl._create_unverified_context()
def probe(ip):
    out = []
    for url in (f"http://{ip}/", f"https://{ip}/"):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "lan-scan"}), timeout=2, context=ctx if url.startswith("https") else None)
            body = r.read(20000).decode("utf-8", "ignore")
            t = re.search(r"<title>([^<]*)", body, re.I)
            out.append(f"{url} {r.status} title={t.group(1).strip() if t else '-'} server={r.headers.get('Server','-')}")
            break
        except Exception as e:
            pass
    return ip, out
with cf.ThreadPoolExecutor(64) as ex:
    for ip, o in ex.map(probe, [f"192.168.0.{i}" for i in range(1, 255)]):
        if o: print(ip, "|", o[0])
print("--- SSDP")
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(1)
msg = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n'
s.sendto(msg.encode(), ("239.255.255.250", 1900))
seen = set(); end = time.time() + 4
while time.time() < end:
    try:
        d, a = s.recvfrom(4096)
    except socket.timeout:
        continue
    t = d.decode("utf-8", "ignore")
    st = re.search(r"^ST:\s*(.*)$", t, re.I | re.M); srv = re.search(r"^SERVER:\s*(.*)$", t, re.I | re.M); loc = re.search(r"^LOCATION:\s*(.*)$", t, re.I | re.M)
    k = (a[0], st.group(1).strip() if st else "")
    if k in seen: continue
    seen.add(k)
    print(a[0], "|", k[1], "|", srv.group(1).strip() if srv else "", "|", loc.group(1).strip() if loc else "")
