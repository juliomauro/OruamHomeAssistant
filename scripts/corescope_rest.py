# corescope_rest.py v1.9 - REP-CASA-4387 (meu repetidor) agora e no no CoreScope
# v1.8 - repetidoras de SP e de Exterior, /health (quem ouve) e lista de vizinhos para todas, canais Public e #exterior da exterior
# v1.7 - no pode vir de outro CoreScope (3o item da tupla = base da API); Exterior/exterior via corescope2.example.org
# v1.6 - gera o bloco rest: do CoreScope (example) para o configuration.yaml do HA
# v1.5: observer em sensores separados (json_attributes_path com filtro nao funciona no HA)
# v1.4: status do observer REP-CASA-4387 (lista de observers filtrada, a cada 10 min)
# v1.3: canal Public da rede inteira (ultimas 20 mensagens, a cada 2 min)
# v1.1: analytics de 7 dias (disponibilidade, sinal, relogio) a cada 3 h e vizinhos a cada 1 h
B0 = B = "https://corescope.example.org/api/nodes/"
SE = "https://corescope2.example.org/api/nodes/"
NOS = {  # slug: (nome, public key)
    "meu_repetidor": ("REP-CASA-4387", "438702360c1a1ef1d268c787a0d19550657478bcc2c48ff9efffca515d168ea6"),
    "amigo": ("REP-AMIGO-07C8", "07c83e98f1fa26b77472a9d9d2f442b8a0006b2a5c312d114af2202c6069598e"),
    "reg_norte": ("REP-NORTE-E28A", "e28a4afe7fd6b5a37cec62c16a182f11cf79bd5ef8ccc0c819f7a5cc292296e0"),
    "reg_sul": ("REP-SUL-786A", "786aa9f74e4516d3dc589d54cd4291175dfc333257c11bfbf74161664d9e862f"),
    "reg_leste": ("REP-LESTE-8A98", "8a9864a4a6bbbc5bbec932c9fcdba4be53286e7c58a52e1a7479f6b34f38529a"),
    "reg_oeste": ("REP-OESTE-E0BD", "e0bd6815ed0b18ed266fee56ce403a855afe1f3bd5b6133d5c1021ca3e0a8a85"),
    "cap_1": ("REP-CAP1-6507", "650771c4e32cd6fdd1f7ec0b63d9e8e61472e19b4e87b361d64c464ed4fdd86c"),
    "cap_2": ("REP-CAP2-BA1D", "ba1dbd5e24987201028a531be17140baedb74a1cf47d0360ace6c199c92bb97f"),
    "cap_3": ("REP-CAP3-94EF", "94ef92b95d59ff1032c11f30f86555cc6e1604927cb438ae2ae8a4e23c6d278e"),
    "cap_4": ("REP-CAP4-B8F7", "b8f7e3962f79ca7fa239bbcbad4378d411fce7a24ed975047fb3239f4782b755"),
    "ext_1": ("REP-EXT1-D42F", "d42f907d864e25dafb6f68e0ba9b508706585b50205ff4ad61cf2e1a638b7603", SE),
    "ext_2": ("REP-EXT2-9EA5", "9ea5c2465ef65ebc8bc9eef7e17b1c2cb6e259bd0fe1fde7616bc3841777aec7", SE),
    "ext_3": ("REP-EXT3-E887", "e887f954bce271b0d25436d21f22f075a8d4d1fb283b5d44aa10a2819136139d", SE),
    "ext_4": ("REP-EXT4-8430", "8430835284e88d76804332cb2740424ad8a2131ff8d1ab9762c44acdaa482e70", SE),
    "ext_5": ("REP-EXT5-81A5", "81a59f75c4a0cdb1217f289475a9f08a30bd92465ac3610ca201a03498368719", SE),
}
ATTRS = ["name", "first_seen", "last_heard", "last_relayed", "relay_count_1h", "relay_active", "usefulness_grade",
         "usefulness_score", "coverage_score", "bridge_score", "redundancy_score", "traffic_share_score",
         "advert_count", "flood_advert_count_7d", "battery_mv", "temperature_c"]
STATS = ["signalGrade", "snrMean", "snrStdDev", "totalPackets", "uniqueObservers", "avgPacketsPerDay",
         "longestSilenceMs", "longestSilenceStart", "relayPct"]

def res(url, scan):
    return [f"  - resource: {url}", f"    scan_interval: {scan}", "    headers:", "      User-Agent: ha-casa/1.0", "    sensor:"]

def sensor(nome, uid, icon, unit, value, path=None, attrs=(), measure=False):
    o = [f"      - name: {nome}", f"        unique_id: {uid}", f"        icon: {icon}"]
    if unit: o.append(f"        unit_of_measurement: \"{unit}\"")
    if measure: o.append("        state_class: measurement")
    o.append(f"        value_template: \"{value}\"")
    if path: o.append(f"        json_attributes_path: \"{path}\"")
    if attrs: o += ["        json_attributes:"] + [f"          - {a}" for a in attrs]
    return o

out = ["  # CoreScope da comunidade (corescope.example.org), so leitura (gerado por corescope_rest.py)"]
for slug, (nome, pk, *base) in NOS.items():
    B = base[0] if base else B0
    u = f"corescope_{slug}"
    out += res(B + pk, 3600) + sensor(f"CoreScope {nome}", u, "mdi:radio-tower", "pacotes",
                                      "{{ value_json.node.relay_count_24h | int(0) }}", "$.node", ATTRS, True)
    out += res(B + pk + "/analytics?days=7", 10800)
    out += sensor(f"CoreScope {slug} disponibilidade", u + "_disponibilidade", "mdi:percent-circle", "%",
                  "{{ value_json.computedStats.availabilityPct }}", "$.computedStats", STATS, True)
    out += sensor(f"CoreScope {slug} relogio", u + "_relogio", "mdi:clock-alert-outline", "min",
                  "{{ ((value_json.clockSkew.lastSkewSec | float(0)) / 60) | round(0) | int }}", "$.clockSkew",
                  ["severity", "driftPerDaySec", "medianSkewSec"])
    out += res(B + pk + "/neighbors", 3600)
    out += sensor(f"CoreScope {slug} vizinhos", u + "_vizinhos", "mdi:account-group", "vizinhos",
                  "{{ value_json.neighbors | length }}", None, ["neighbors"], True)
    out += sensor(f"CoreScope {slug} melhor vizinho", u + "_melhor_vizinho", "mdi:star-circle",
                  None, "{% set l = value_json.neighbors | sort(attribute='count', reverse=true) | list %}"
                  "{{ (l[0].name ~ ' (' ~ (l[0].distance_km | default(0) | round(1)) ~ ' km)')[:250] if l else '-' }}")
    out += res(B + pk + "/health", 3600) + sensor(f"CoreScope {slug} observers", u + "_observers", "mdi:ear-hearing",
                                                  "observers", "{{ value_json.observers | length }}", None, ["observers", "stats"], True)
out += res("https://corescope.example.org/api/channels/Public/messages?limit=20", 120)
out += sensor("CoreScope canal Public", "corescope_public", "mdi:forum", None,
              "{{ (value_json.messages | last).packetHash if value_json.messages else '-' }}", None, ["messages", "total"])
for slug_c, canal in (("ext_public", "Public"), ("ext_local", "%23exterior")):
    out += res("https://corescope2.example.org/api/channels/" + canal + "/messages?limit=20", 120)
    out += sensor(f"CoreScope canal {slug_c}", "corescope_canal_" + slug_c, "mdi:forum", None,
                  "{{ (value_json.messages | last).packetHash if value_json.messages else '-' }}", None, ["messages", "total"])
OBS = "438702360C1A1EF1D268C787A0D19550657478BCC2C48FF9EFFFCA515D168EA6"
SEL = "value_json.observers | selectattr('id', 'eq', OBS) | list"
out += res("https://corescope.example.org/api/observers", 600)
def obs(campo, padrao="none"):
    return ("{% set o = SEL %}{{ o[0].CAMPO if o and o[0].CAMPO not in [None, 'None'] else PADRAO }}"
            .replace("SEL", SEL).replace("OBS", "'" + OBS + "'").replace("CAMPO", campo).replace("PADRAO", padrao))
out += sensor("CoreScope meu observer", "corescope_meu_observer", "mdi:antenna", "pacotes/h",
              obs("packetsLastHour", "0"), measure=True)
out += sensor("CoreScope meu observer ultimo pacote", "corescope_meu_observer_ultimo_pacote", "mdi:package-up", None,
              obs("last_packet_at"))
out += sensor("CoreScope meu observer visto", "corescope_meu_observer_visto", "mdi:wifi-check", None,
              obs("last_seen"))
out += sensor("CoreScope meu observer total", "corescope_meu_observer_total", "mdi:counter", "pacotes",
              obs("packet_count", "0"))
out += sensor("CoreScope meu observer firmware", "corescope_meu_observer_firmware", "mdi:chip", None,
              obs("firmware", "'-'"))
print("\n".join(out))
