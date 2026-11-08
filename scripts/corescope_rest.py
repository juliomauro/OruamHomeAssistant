# corescope_rest.py v1.6 - gera o bloco rest: do CoreScope (comunidade) para o configuration.yaml do HA
# v1.5: observer em sensores separados (json_attributes_path com filtro nao funciona no HA)
# v1.4: status do observer REP-CASA-4387 (lista de observers filtrada, a cada 10 min)
# v1.3: canal Public da rede inteira (ultimas 20 mensagens, a cada 2 min)
# v1.1: analytics de 7 dias (disponibilidade, sinal, relogio) a cada 3 h e vizinhos a cada 1 h
B = "https://corescope.example.org/api/nodes/"
NOS = {  # slug: (nome, public key)
    "amigo": ("REP-AMIGO-07C8", "07c82d5f55575b0f419bbb39539f3c8716d3151dc4936774f90a24c37669696c"),
    "reg_norte": ("REP-NORTE-E28A", "e28aa90ba6b7662ec246d5a5acfea8e215255d0108941e9774ad92ac304096c9"),
    "reg_sul": ("REP-SUL-786A", "786a4678d64f794dcfa4d7f55b9bb31c852b0cf346ab931396cca976e9ede9cc"),
    "reg_leste": ("REP-LESTE-8A98", "8a98e225772e059b75c4e98dad2115c9a2dab344a825638090302827e04b1bde"),
    "reg_oeste": ("REP-OESTE-E0BD", "e0bda5037f6ca6f616d8670147fb60356f47e3cb61563a43488c9aba310a7863"),
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
for slug, (nome, pk) in NOS.items():
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
                  "{{ value_json.neighbors | length }}", None, ["neighbors"] if slug == "amigo" else (), True)
    out += sensor(f"CoreScope {slug} melhor vizinho", u + "_melhor_vizinho", "mdi:star-circle",
                  None, "{% set l = value_json.neighbors | sort(attribute='count', reverse=true) | list %}"
                  "{{ (l[0].name ~ ' (' ~ (l[0].distance_km | default(0) | round(1)) ~ ' km)')[:250] if l else '-' }}")
pk = NOS["amigo"][1]
out += res(B + pk + "/health", 3600) + sensor("CoreScope amigo observers", "corescope_amigo_observers", "mdi:ear-hearing",
                                              "observers", "{{ value_json.observers | length }}", None, ["observers", "stats"])
out += res("https://corescope.example.org/api/channels/Public/messages?limit=20", 120)
out += sensor("CoreScope canal Public", "corescope_public", "mdi:forum", None,
              "{{ (value_json.messages | last).packetHash if value_json.messages else '-' }}", None, ["messages", "total"])
OBS = "43879F79CD8738BB68F9C85809B821247D00D3419308D636E651B6E203726AAA"
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
