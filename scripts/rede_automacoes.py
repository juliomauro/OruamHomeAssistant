# rede_automacoes.py v1.0 - renomeia o ping do observer e cria automacoes de Wi-Fi
# uso: python3 rede_automacoes.py <token>  (roda no atlas)
import os, json, sys, urllib.request
T = sys.argv[1]; B = os.environ.get("HA_URL", "http://127.0.0.1:8123") + "/api"
def req(m, p, body=None):
    r = urllib.request.Request(B + p, method=m, data=json.dumps(body).encode() if body is not None else None,
                               headers={"Authorization": "Bearer " + T, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as x: return json.loads(x.read() or "null")
AUTOS = {
    "wifi_aparelho_novo": {
        "alias": "Wi-Fi: aparelho novo",
        "description": "Avisa quando um MAC nunca visto conecta em algum Deco (a integracao cria a entidade uma vez por MAC).",
        "mode": "queued",
        "triggers": [{"trigger": "event", "event_type": "entity_registry_updated", "event_data": {"action": "create"}}],
        "conditions": [{"condition": "template", "value_template": "{{ trigger.event.data.entity_id is match('device_tracker\\.(sala|office)_deco_') }}"}],
        "actions": [{"action": "persistent_notification.create", "data": {
            "notification_id": "wifi_novo_{{ trigger.event.data.entity_id.split('.')[1] }}",
            "title": "Aparelho novo no Wi-Fi",
            "message": "{% set e = trigger.event.data.entity_id %}Apareceu **{{ e.split('.')[1] | regex_replace('^(sala|office)_deco_', '') }}** no Deco {{ 'Sala' if 'sala_deco' in e else 'Office' }} em {{ now().strftime('%d/%m %H:%M') }}.\n\nEntidade: `{{ e }}` (desligada por padrão). Se não reconhecer o aparelho, confira no app Deco e bloqueie por lá."}}],
    },
    "observer_wifi": {
        "alias": "MeshCore: observer no Wi-Fi",
        "description": "Avisa quando o REP-CASA-4387 (reserva .27) entra ou sai do Wi-Fi.",
        "mode": "single",
        "triggers": [
            {"trigger": "state", "entity_id": "binary_sensor.rede_observer", "from": "off", "to": "on", "id": "on"},
            {"trigger": "state", "entity_id": "binary_sensor.rede_observer", "from": "on", "to": "off", "for": {"minutes": 10}, "id": "off"}],
        "actions": [{"action": "persistent_notification.create", "data": {
            "notification_id": "observer_wifi",
            "title": "Observer MeshCore",
            "message": "{{ 'Conectou no Wi-Fi (192.168.0.27) em ' if trigger.id == 'on' else 'Saiu do Wi-Fi há 10 min, desde ' }}{{ now().strftime('%d/%m %H:%M') }}."}}],
    },
}
for aid, cfg in AUTOS.items():
    print(aid, req("POST", f"/config/automation/config/{aid}", {"id": aid, **cfg}))
