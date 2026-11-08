# telegram_automacoes.py v1.3 (bom dia, servidores, chuva) - alertas e comandos da casa via Telegram (aparelho novo, porta, internet, observer, impressora, Deco)
# uso: python3 telegram_automacoes.py <token>  (roda no atlas)
import os, json, sys, urllib.request
T = sys.argv[1]; B = os.environ.get("HA_URL", "http://127.0.0.1:8123") + "/api"
ENTRY = os.environ.get("TG_ENTRY", "SEU_CONFIG_ENTRY_ID")  # entry_id da integracao Telegram bot
CHAT = int(os.environ.get("TG_CHAT", "123456789"))  # seu chat_id (o mesmo liberado em allowed_chat_ids)
def req(m, p, body=None):
    r = urllib.request.Request(B + p, method=m, data=json.dumps(body).encode() if body is not None else None,
                               headers={"Authorization": "Bearer " + T, "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as x: return json.loads(x.read() or "null")
NOME = "{{ trigger.event.data.entity_id.split('.')[1] | regex_replace('^(sala|office)_deco_', '') }}"
DECO = "{{ 'Sala' if 'sala_deco' in trigger.event.data.entity_id else 'Office' }}"
AUTOS = {
    "wifi_aparelho_novo": {
        "alias": "Wi-Fi: aparelho novo",
        "description": "Avisa (HA + Telegram) quando um MAC nunca visto conecta em algum Deco. A integracao cria a entidade uma vez por MAC.",
        "mode": "queued",
        "triggers": [{"trigger": "event", "event_type": "entity_registry_updated", "event_data": {"action": "create"}}],
        "conditions": [{"condition": "template", "value_template": "{{ trigger.event.data.entity_id is match('device_tracker\\.(sala|office)_deco_') }}"}],
        "actions": [
            {"action": "persistent_notification.create", "data": {
                "notification_id": "wifi_novo_{{ trigger.event.data.entity_id.split('.')[1] }}",
                "title": "Aparelho novo no Wi-Fi",
                "message": "Apareceu **" + NOME + "** no Deco " + DECO + " em {{ now().strftime('%d/%m %H:%M') }}.\n\nEntidade: `{{ trigger.event.data.entity_id }}` (desligada por padrão)."}},
            {"action": "telegram_bot.send_message", "continue_on_error": True, "data": {
                "config_entry_id": ENTRY, "target": CHAT, "parse_mode": "html",
                "title": "📶 Aparelho novo no Wi-Fi",
                "message": "<b>" + NOME + "</b>\nDeco " + DECO + " · {{ now().strftime('%d/%m %H:%M') }}\n\nVocê reconhece esse aparelho?",
                "inline_keyboard": [
                    "✅ Conheço:/wifi_conheco " + NOME + ", 🚫 Como bloquear?:/wifi_bloquear " + NOME]}},
        ],
    },
    "telegram_botoes_wifi": {
        "alias": "Telegram: botões do alerta de Wi-Fi",
        "description": "Trata os botoes Conheco / Como bloquear do alerta de aparelho novo.",
        "mode": "parallel",
        "triggers": [{"trigger": "event", "event_type": "telegram_callback"}],
        "conditions": [
            {"condition": "template", "value_template": "{{ trigger.event.data.data is match('/wifi_(conheco|bloquear) ') }}"},
            {"condition": "template", "value_template": "{{ trigger.event.data.user_id | int(0) == " + str(CHAT) + " }}"}],
        "actions": [
            {"variables": {"cmd": "{{ trigger.event.data.data.split(' ')[0] }}",
                           "nome": "{{ trigger.event.data.data.split(' ', 1)[1] }}"}},
            {"choose": [
                {"conditions": [{"condition": "template", "value_template": "{{ cmd == '/wifi_conheco' }}"}],
                 "sequence": [
                     {"action": "telegram_bot.answer_callback_query", "data": {
                         "config_entry_id": ENTRY, "callback_query_id": "{{ trigger.event.data.id }}", "message": "Anotado ✅"}},
                     {"action": "telegram_bot.edit_message", "data": {
                         "config_entry_id": ENTRY, "chat_id": "{{ trigger.event.data.chat_id }}",
                         "message_id": "{{ trigger.event.data.message.message_id }}", "parse_mode": "html",
                         "title": "📶 Aparelho novo no Wi-Fi",
                         "message": "<b>{{ nome }}</b>\n✅ Marcado como conhecido em {{ now().strftime('%d/%m %H:%M') }}.\nMe diga o nome dele no Claude para eu renomear no painel."}},
                     {"action": "persistent_notification.dismiss", "data": {"notification_id": "wifi_novo_{{ nome }}"}}]},
                {"conditions": [{"condition": "template", "value_template": "{{ cmd == '/wifi_bloquear' }}"}],
                 "sequence": [
                     {"action": "telegram_bot.answer_callback_query", "data": {
                         "config_entry_id": ENTRY, "callback_query_id": "{{ trigger.event.data.id }}", "message": "Instruções abaixo"}},
                     {"action": "telegram_bot.send_message", "data": {
                         "config_entry_id": ENTRY, "target": "{{ trigger.event.data.chat_id }}", "parse_mode": "html",
                         "message": "🚫 <b>Bloquear {{ nome }}</b>\n\nApp <b>Deco</b> > <b>Clientes</b> > toque em <b>{{ nome }}</b> > <b>Bloquear</b>.\n\nDepois troque a senha do Wi-Fi se achar que alguém descobriu."}}]},
            ]},
        ],
    },
}
def tg(msg, **kw):
    return {"action": "telegram_bot.send_message", "continue_on_error": True,
            "data": {"config_entry_id": ENTRY, "target": kw.pop("target", CHAT), "parse_mode": "html", "message": msg, **kw}}
def resp(msg, **kw):  # responde no chat de quem mandou o comando
    return tg(msg, target="{{ trigger.event.data.chat_id }}", **kw)

LUZES = ["switch.sala_principal", "switch.sala_atelier", "switch.sala_mesa_de_jantar", "switch.sala_lateral", "switch.sala_balcao",
         "switch.sala_de_estar_led_da_escada_switch_1", "switch.escritorio_teto_switch_1", "switch.escritorio_led_escritorio_switch_1",
         "switch.quintal_lateral", "switch.quintal_fundo"]
LST = json.dumps(LUZES).replace('"', "'")
NET_ON = "(is_state('binary_sensor.rede_cloudflare', 'on') or is_state('binary_sensor.rede_google', 'on'))"
OP = "escritorio_octoprint"
STATUS = (
    "🏠 <b>Casa</b> · {{ now().strftime('%d/%m %H:%M') }}\n\n"
    "🚪 Porta: {{ 'ABERTA' if is_state('binary_sensor.entrada_porta_de_entrada_porta', 'on') else 'fechada' }}\n"
    "🌐 Internet: {% if " + NET_ON + " %}ok · {{ states('sensor.rede_cloudflare_latencia') | float(0) | round(0) | int }} ms · ↓ {{ states('sensor.internet_download') | float(0) | round(0) | int }} Mbit/s{% else %}FORA DO AR{% endif %}\n"
    "💡 Luzes: {% set l = expand(" + LST + ") | selectattr('state', 'eq', 'on') | map(attribute='name') | list %}{{ 'todas apagadas' if not l else l | join(', ') }}\n"
    "🌡️ Cozinha: {{ states('sensor.cozinha_casa_temperatura') | float(0) | round(1) }}° · {{ states('sensor.cozinha_casa_umidade') | float(0) | round(0) | int }}%\n"
    "🤖 Rubi: {{ {'cleaning': 'limpando', 'docked': 'na base', 'returning': 'voltando', 'idle': 'parado', 'paused': 'pausado', 'error': 'ERRO'}.get(states('vacuum.sala_de_estar_rubi'), states('vacuum.sala_de_estar_rubi')) }} · {{ states('sensor.sala_de_estar_rubi_bateria') | float(0) | int }}%\n"
    "🖨️ Impressora: {% if is_state('binary_sensor.OP_printing', 'on') %}{{ states('sensor.OP_job_percentage') | int(0) }}%, termina {{ as_timestamp(states('sensor.OP_estimated_finish_time'), 0) | timestamp_custom('%H:%M') }}{% elif states('sensor.OP_current_state') in ['unavailable', 'unknown'] %}desligada{% else %}parada{% endif %}\n"
    "📶 Wi-Fi: {{ states('sensor.deco_sala_connected_clients') }} na Sala, {{ states('sensor.deco_office_connected_clients') }} no Office\n"
    "📅 Próximo: {% set ev = (state_attr('sensor.agenda_hoje', 'eventos') or []) | selectattr('ts', 'gt', now().timestamp()) | rejectattr('dia_todo') | list %}"
    "{% if ev %}{% set e = ev[0] %}{% set dia = (e.ts | timestamp_custom('%Y-%m-%d')) %}"
    "<b>{{ 'hoje' if dia == now().strftime('%Y-%m-%d') else 'amanhã' }} {{ e.ts | timestamp_custom('%H:%M') }}</b> {{ e.titulo }}"
    "{% else %}nada até amanhã{% endif %}"
).replace("OP_", OP + "_")
REDE = (
    "📶 <b>Quem está no Wi-Fi</b>\n"
    "{% set banda = {'band2_4': '2,4', 'band5': '5G', 'wired': 'cabo'} %}"
    "{% for d in ['Sala', 'Office'] %}{% set l = states.device_tracker | selectattr('entity_id', 'match', 'device_tracker.wifi_') | selectattr('state', 'eq', 'home') | selectattr('attributes.deco_device', 'eq', d) | sort(attribute='name') | list %}"
    "\n<b>Deco {{ d }}</b> ({{ l | count }})\n{% for s in l %}• {{ s.name | regex_replace('^(Sala|Office) Deco ', '') }} <i>{{ banda.get(s.attributes.connection_type, '') }}</i>\n{% endfor %}{% endfor %}"
)
AGENDA = (
    "{% set ev = state_attr('sensor.agenda_hoje', 'eventos') or [] %}{% set ini = as_timestamp(today_at()) %}"
    "{% macro linha(e) %}• {% if e.dia_todo %}dia todo{% else %}<b>{{ e.ts | timestamp_custom('%H:%M') }}</b>{% endif %} {{ e.titulo }} <i>({{ e.agenda }})</i>{% endmacro %}"
    "📅 <b>Hoje</b>\n{% for e in ev | selectattr('ts', 'lt', ini + 86400) | selectattr('te', 'gt', now().timestamp()) %}{{ linha(e) }}\n{% else %}nada mais hoje\n{% endfor %}"
    "\n📅 <b>Amanhã</b>\n{% for e in ev | selectattr('ts', 'lt', ini + 172800) | selectattr('te', 'gt', ini + 86400) %}{{ linha(e) }}\n{% else %}nada marcado\n{% endfor %}"
)
AJUDA = ("🤖 <b>Comandos</b>\n/status · resumo da casa\n/rede · quem está no Wi-Fi\n/agenda · hoje e amanhã\n"
         "/speedtest · mede a internet agora\n/apagar · apaga todas as luzes (pede confirmação)")

def cmd(nome, *seq):
    return {"conditions": [{"condition": "template", "value_template": "{{ trigger.event.data.command | regex_replace('@.*', '') == '" + nome + "' }}"}],
            "sequence": list(seq)}

AUTOS["telegram_comandos"] = {
    "alias": "Telegram: comandos da casa",
    "description": "Comandos /status /rede /agenda /speedtest /apagar /ajuda. So responde ao chat liberado.",
    "mode": "queued",
    "triggers": [{"trigger": "event", "event_type": "telegram_command"}],
    "conditions": [{"condition": "template", "value_template": "{{ trigger.event.data.user_id | int(0) == " + str(CHAT) + " }}"}],
    "actions": [{"choose": [
        cmd("/status", resp(STATUS)),
        cmd("/rede", resp(REDE)),
        cmd("/agenda", {"event": "agenda_atualizar"}, {"delay": {"seconds": 3}}, resp(AGENDA)),
        cmd("/speedtest", resp("⏱️ Medindo a internet, leva uns 30 segundos..."),
            {"action": "homeassistant.update_entity", "target": {"entity_id": "sensor.internet_download"}, "continue_on_error": True},
            {"delay": {"seconds": 5}},
            resp("🚀 <b>Speedtest</b>\n↓ {{ states('sensor.internet_download') | float(0) | round(0) | int }} Mbit/s\n↑ {{ states('sensor.internet_upload') | float(0) | round(0) | int }} Mbit/s\nping {{ states('sensor.internet_ping') | float(0) | round(0) | int }} ms")),
        cmd("/apagar", resp("{% set l = expand(" + LST + ") | selectattr('state', 'eq', 'on') | map(attribute='name') | list %}"
                            "{% if l %}💡 Acesas: {{ l | join(', ') }}\n\nApagar todas?{% else %}💡 Já está tudo apagado.{% endif %}",
                            inline_keyboard=["✅ Apagar tudo:/casa_apagar, ❌ Cancelar:/casa_cancelar"])),
    ], "default": [resp(AJUDA)]}],
}
AUTOS["telegram_botoes_casa"] = {
    "alias": "Telegram: botões da casa",
    "description": "Confirmacao do /apagar.",
    "mode": "parallel",
    "triggers": [{"trigger": "event", "event_type": "telegram_callback"}],
    "conditions": [
        {"condition": "template", "value_template": "{{ trigger.event.data.data in ['/casa_apagar', '/casa_cancelar'] }}"},
        {"condition": "template", "value_template": "{{ trigger.event.data.user_id | int(0) == " + str(CHAT) + " }}"}],
    "actions": [
        {"if": [{"condition": "template", "value_template": "{{ trigger.event.data.data == '/casa_apagar' }}"}],
         "then": [{"action": "homeassistant.turn_off", "target": {"entity_id": LUZES}, "continue_on_error": True}]},
        {"action": "telegram_bot.answer_callback_query", "data": {"config_entry_id": ENTRY, "callback_query_id": "{{ trigger.event.data.id }}",
                                                                   "message": "{{ 'Apagando' if trigger.event.data.data == '/casa_apagar' else 'Cancelado' }}"}},
        {"action": "telegram_bot.edit_message", "data": {"config_entry_id": ENTRY, "chat_id": "{{ trigger.event.data.chat_id }}",
                                                          "message_id": "{{ trigger.event.data.message.message_id }}",
                                                          "message": "{{ '💡 Luzes apagadas às ' ~ now().strftime('%H:%M') if trigger.event.data.data == '/casa_apagar' else 'Cancelado, nada foi apagado.' }}"}},
    ],
}
AUTOS["telegram_internet"] = {
    "alias": "Telegram: internet voltou",
    "description": "Quando a internet volta depois de 2+ min fora, avisa quanto tempo ficou fora (durante a queda o Telegram nao chega).",
    "mode": "single",
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.rede_cloudflare", "from": "off", "to": "on"}],
    "conditions": [{"condition": "template", "value_template": "{{ (now() - trigger.from_state.last_changed).total_seconds() > 120 }}"}],
    "actions": [{"delay": {"seconds": 20}},
                tg("🌐 <b>Internet voltou</b>\nFicou fora das {{ as_local(trigger.from_state.last_changed).strftime('%H:%M') }} às {{ as_local(trigger.to_state.last_changed).strftime('%H:%M') }} "
                   "({{ ((trigger.to_state.last_changed - trigger.from_state.last_changed).total_seconds() / 60) | round(0) | int }} min)."
                   "{{ '\nO modem também caiu.' if is_state('binary_sensor.rede_modem', 'on') and (now() - states.binary_sensor.rede_modem.last_changed).total_seconds() < 600 else '' }}")],
}
AUTOS["telegram_impressora"] = {
    "alias": "Telegram: impressão terminou",
    "mode": "single",
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.OP_printing".replace("OP", OP), "from": "on", "to": "off"}],
    "actions": [tg("🖨️ <b>Impressão terminou</b>\n{{ states('sensor.OP_current_file') }} às {{ now().strftime('%H:%M') }}{{ ' (com erro!)' if is_state('binary_sensor.OP_printing_error', 'on') }}".replace("OP_", OP + "_"))],
}
AUTOS["telegram_deco_offline"] = {
    "alias": "Telegram: Deco offline",
    "mode": "queued",
    "triggers": [{"trigger": "state", "entity_id": ["binary_sensor.deco_sala_online", "binary_sensor.deco_office_online"], "from": "on", "to": "off", "for": {"minutes": 3}},
                 {"trigger": "state", "entity_id": ["binary_sensor.deco_sala_online", "binary_sensor.deco_office_online"], "from": "off", "to": "on", "id": "volta"}],
    "conditions": [{"condition": "template", "value_template": "{{ trigger.id != 'volta' or (now() - trigger.from_state.last_changed).total_seconds() > 180 }}"}],
    "actions": [tg("{{ ('✅ <b>' ~ trigger.to_state.name ~ '</b> voltou') if trigger.id == 'volta' else ('⚠️ <b>' ~ trigger.to_state.name ~ '</b> está offline há 3 min') }}")],
}

COND = ("{% set pt = {'clear-night': 'céu limpo', 'cloudy': 'nublado', 'fog': 'neblina', 'hail': 'granizo', 'lightning': 'raios', "
        "'lightning-rainy': 'chuva com raios', 'partlycloudy': 'parcialmente nublado', 'pouring': 'chuva forte', 'rainy': 'chuva', "
        "'snowy': 'neve', 'snowy-rainy': 'neve e chuva', 'sunny': 'sol', 'windy': 'vento', 'windy-variant': 'vento e nuvens', 'exceptional': 'tempo extremo'} %}")
SERV_PROBLEMAS = (
    "{% set p = namespace(l=[]) %}"
    "{% for e, n in [('sensor.atlas_4tb', 'Disco 4 TB'), ('sensor.atlas_disco', 'Disco do atlas'), ('sensor.boreas_disco', 'Disco do boreas')] %}"
    "{% if states(e) | float(0) > 85 %}{% set p.l = p.l + [n ~ ' em ' ~ states(e) | float(0) | round(0) | int ~ '%'] %}{% endif %}{% endfor %}"
    "{% if states('sensor.boreas_cpu') in ['unavailable', 'unknown'] %}{% set p.l = p.l + ['boreas sem resposta'] %}{% endif %}"
    "{% if not is_state('binary_sensor.traefik_online', 'on') %}{% set p.l = p.l + ['Traefik fora do ar'] %}{% endif %}"
    "{% if not is_state('switch.pihole', 'on') %}{% set p.l = p.l + ['Pi-hole sem bloqueio'] %}{% endif %}"
    "{% set c = ((as_datetime(states('sensor.traefik_certificado')) - now()).days) if as_datetime(states('sensor.traefik_certificado')) else 999 %}"
    "{% if c < 20 %}{% set p.l = p.l + ['certificado vence em ' ~ c ~ ' dias'] %}{% endif %}"
)
BOM_DIA = (
    COND +
    "{% set d = ['segunda','terça','quarta','quinta','sexta','sábado','domingo'] %}"
    "{% set m = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'] %}"
    "☀️ <b>Bom dia!</b> {{ d[now().weekday()] | capitalize }}, {{ now().day }} de {{ m[now().month - 1] }}\n\n"
    "{% set h = dia['weather.casa'].forecast[0] %}"
    "🌦️ <b>Tempo:</b> {{ pt.get(h.condition, h.condition) }}, {{ h.templow | round(0) | int }}° a {{ h.temperature | round(0) | int }}°"
    "{% set ch = hora['weather.casa'].forecast | selectattr('precipitation', 'ge', 0.3) | list %}"
    "{% set ch = ch | selectattr('datetime', 'lt', (today_at() + timedelta(days=1)).isoformat()) | list %}"
    "{% if ch %}\n☔ Chuva prevista entre {{ as_local(as_datetime(ch[0].datetime)).strftime('%Hh') }} e "
    "{{ (as_local(as_datetime(ch[-1].datetime)) + timedelta(hours=1)).strftime('%Hh') }} ({{ ch | sum(attribute='precipitation') | round(1) }} mm){% else %}, sem chuva{% endif %}\n\n"
    "{% set ev = state_attr('sensor.agenda_hoje', 'eventos') or [] %}{% set ini = as_timestamp(today_at()) %}"
    "📅 <b>Hoje</b>\n{% for e in ev | selectattr('ts', 'lt', ini + 86400) | selectattr('te', 'gt', ini) %}"
    "• {% if e.dia_todo %}{{ e.titulo }}{% else %}<b>{{ e.ts | timestamp_custom('%H:%M') }}</b> {{ e.titulo }}{% endif %}\n"
    "{% else %}agenda livre\n{% endfor %}\n"
    "{% set n = state_attr('sensor.diario_da_noite', 'eventos') or [] %}"
    "🌙 <b>Noite</b>: {% if n %}\n{% for x in n %}• {{ x }}\n{% endfor %}{% else %}tranquila\n{% endif %}\n"
    "🌐 Internet: ↓ {{ states('sensor.internet_download') | float(0) | round(0) | int }} ↑ {{ states('sensor.internet_upload') | float(0) | round(0) | int }} Mbit/s\n"
    + SERV_PROBLEMAS +
    "🖥️ Servidores: {{ 'tudo ok' if not p.l else p.l | join(', ') }}"
)
AUTOS["telegram_bom_dia"] = {
    "alias": "Telegram: bom dia",
    "description": "Resumo diario as 7:30: tempo, chuva, agenda, o que aconteceu de noite, internet e servidores.",
    "mode": "single",
    "triggers": [{"trigger": "time", "at": "07:30:00"}, {"trigger": "event", "event_type": "bom_dia_teste"}],
    "actions": [
        {"event": "agenda_atualizar"}, {"delay": {"seconds": 3}},
        {"action": "weather.get_forecasts", "target": {"entity_id": "weather.casa"}, "data": {"type": "daily"}, "response_variable": "dia"},
        {"action": "weather.get_forecasts", "target": {"entity_id": "weather.casa"}, "data": {"type": "hourly"}, "response_variable": "hora"},
        tg(BOM_DIA)],
}
AUTOS["telegram_chuva"] = {
    "alias": "Telegram: chuva chegando",
    "mode": "single",
    "triggers": [{"trigger": "state", "entity_id": "binary_sensor.chuva_chegando", "from": "off", "to": "on"}],
    "conditions": [{"condition": "time", "after": "07:00:00", "before": "22:30:00"},
                   {"condition": "template", "value_template": "{{ this.attributes.last_triggered is none or (now() - this.attributes.last_triggered).total_seconds() > 10800 }}"}],
    "actions": [tg("🌧️ <b>Chuva chegando</b>{{ ' por volta das ' ~ state_attr('binary_sensor.chuva_chegando', 'inicio') if state_attr('binary_sensor.chuva_chegando', 'inicio') else '' }}"
                   " ({{ state_attr('binary_sensor.chuva_chegando', 'mm_3h') }} mm nas próximas horas).\nRoupa no varal? Janelas abertas?")],
}
SERV_MSG = (
    "{% set t = trigger.id %}"
    "{% if t == 'disco' %}💾 <b>{{ trigger.to_state.name }}</b> passou de 90%: {{ trigger.to_state.state | float(0) | round(0) | int }}%"
    "{% elif t == 'temp' %}🔥 <b>{{ trigger.to_state.name }}</b> em {{ trigger.to_state.state }}°C há 10 min"
    "{% elif t == 'boreas_off' %}🖥️ <b>boreas</b> sem resposta há 5 min"
    "{% elif t == 'boreas_on' %}✅ <b>boreas</b> voltou"
    "{% elif t == 'traefik_off' %}🔀 <b>Traefik</b> fora do ar há 3 min (*.example.com parado)"
    "{% elif t == 'traefik_on' %}✅ <b>Traefik</b> voltou"
    "{% elif t == 'pihole' %}🛡️ <b>Pi-hole</b> sem bloquear há 30 min"
    "{% elif t == 'cert' %}🔐 Certificado <b>*.example.com</b> vence em {{ (as_datetime(states('sensor.traefik_certificado')) - now()).days }} dias"
    "{% elif t == 'boot' %}🔄 <b>atlas</b> reiniciou às {{ as_local(as_datetime(states('sensor.atlas_ligado_desde'))).strftime('%H:%M') }}"
    "{% endif %}"
)
AUTOS["telegram_servidores"] = {
    "alias": "Telegram: saúde dos servidores",
    "mode": "queued",
    "triggers": [
        {"trigger": "numeric_state", "entity_id": ["sensor.atlas_4tb", "sensor.atlas_disco", "sensor.boreas_disco"], "above": 90, "id": "disco"},
        {"trigger": "numeric_state", "entity_id": ["sensor.atlas_temperatura", "sensor.boreas_temperatura"], "above": 80, "for": {"minutes": 10}, "id": "temp"},
        {"trigger": "state", "entity_id": "sensor.boreas_cpu", "to": "unavailable", "for": {"minutes": 5}, "id": "boreas_off"},
        {"trigger": "state", "entity_id": "sensor.boreas_cpu", "from": "unavailable", "id": "boreas_on"},
        {"trigger": "state", "entity_id": "binary_sensor.traefik_online", "from": "on", "to": "off", "for": {"minutes": 3}, "id": "traefik_off"},
        {"trigger": "state", "entity_id": "binary_sensor.traefik_online", "from": "off", "to": "on", "id": "traefik_on"},
        {"trigger": "state", "entity_id": "switch.pihole", "from": "on", "to": "off", "for": {"minutes": 30}, "id": "pihole"},
        {"trigger": "time", "at": "10:00:00", "id": "cert"},
        {"trigger": "homeassistant", "event": "start", "id": "boot"},
    ],
    "conditions": [{"condition": "template", "value_template":
        "{% set t = trigger.id %}"
        "{% if t == 'cert' %}{{ as_datetime(states('sensor.traefik_certificado')) is not none and (as_datetime(states('sensor.traefik_certificado')) - now()).days < 20 }}"
        "{% elif t == 'boot' %}{{ as_datetime(states('sensor.atlas_ligado_desde')) is not none and (now() - as_datetime(states('sensor.atlas_ligado_desde'))).total_seconds() < 1200 }}"
        "{% elif t == 'boreas_on' %}{{ (now() - trigger.from_state.last_changed).total_seconds() > 300 }}"
        "{% elif t == 'traefik_on' %}{{ (now() - trigger.from_state.last_changed).total_seconds() > 180 }}"
        "{% else %}true{% endif %}"}],
    "actions": [{"delay": {"seconds": "{{ 60 if trigger.id == 'boot' else 0 }}"}}, tg(SERV_MSG)],
}

def acrescenta_tg(aid, step):
    cfg = req("GET", f"/config/automation/config/{aid}")
    if any(a.get("action") == "telegram_bot.send_message" for a in cfg["actions"]):
        print(aid, "ja tem telegram"); return
    cfg["actions"].insert(0, step)
    print(aid, "+telegram", req("POST", f"/config/automation/config/{aid}", cfg))

for aid, cfg in AUTOS.items():
    print(aid, req("POST", f"/config/automation/config/{aid}", {"id": aid, **cfg}))
acrescenta_tg("porta_aberta_madrugada", tg("🚪 <b>Porta aberta</b> às {{ now().strftime('%H:%M') }}"))
acrescenta_tg("observer_wifi", tg("📡 <b>Observer MeshCore</b>\n{{ 'Conectou no Wi-Fi (192.168.0.27)' if trigger.id == 'on' else 'Saiu do Wi-Fi há 10 min' }} · {{ now().strftime('%H:%M') }}"))
