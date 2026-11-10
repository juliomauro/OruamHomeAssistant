# rede_automacoes.py v1.2 (observer: so avisa apos 2 h sem resposta)
# v1.1 (observer: so avisa que voltou se ficou >=10 min fora)
# v1.0 - renomeia o ping do observer e cria automacoes de Wi-Fi
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
        "description": "Avisa quando o REP-CASA-4387 (reserva .27) fica sem responder ao ping por 2 h seguidas, e quando volta depois disso.",
        "mode": "single",
        "triggers": [
            {"trigger": "state", "entity_id": "binary_sensor.rede_observer", "from": "off", "to": "on", "id": "on"},
            {"trigger": "state", "entity_id": "binary_sensor.rede_observer", "from": "on", "to": "off", "for": {"hours": 2}, "id": "off"}],
        "conditions": [{"condition": "template", "value_template": "{{ trigger.id == 'off' or (trigger.to_state.last_changed - trigger.from_state.last_changed).total_seconds() >= 7200 }}"}],
        "actions": [{"action": "persistent_notification.create", "data": {
            "notification_id": "observer_wifi",
            "title": "Observer MeshCore",
            "message": "{{ 'Voltou a responder (192.168.0.27) em ' if trigger.id == 'on' else 'Sem resposta há 2 h, desde ' }}{{ now().strftime('%d/%m %H:%M') }}."}}],
    },
}
for aid, cfg in AUTOS.items():
    print(aid, req("POST", f"/config/automation/config/{aid}", {"id": aid, **cfg}))
