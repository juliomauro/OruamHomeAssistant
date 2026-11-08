# painel_tablet.py v3.2 - painel "Central" para o tablet da sala (horizontal, tela unica estilo Echo Show)
# v3.2: borda e arredondamento direto em cada card (o panel zera e o restore do tema nao pega), previsao com 4 dias.
# v3.1: menos padding nos cards (texto nao corta), Rubi so mostra bateria < 100%, clima sem card_mod.
# v3.0: feito para a tela real do tablet (~1000x600 CSS, sobra ~940x470 com barra lateral e cabecalho):
#       view panel + horizontal-stack (3 colunas fixas, sections nao cabe: minimo 320 px por coluna),
#       fontes e cards compactos, agenda limitada a 4 + 3 eventos. Gap e arredondamento vem do tema.
# v2.1: fontes no ha-tile-info. v2.0: tema escuro "Central escuro", circulo nos icones, som recolhe desligado
# Uso: python3 painel_tablet.py [--create] > cmds.json
import json, sys

PORTA = "binary_sensor.entrada_porta_de_entrada_porta"
LUZES_SALA = [  # entity, nome, icone
    ("switch.sala_principal", "Principal", "mdi:ceiling-light"),
    ("switch.sala_atelier", "Atelier", "mdi:palette"),
    ("switch.sala_mesa_de_jantar", "Jantar", "mdi:silverware-fork-knife"),
    ("switch.sala_lateral", "Lateral", "mdi:wall-sconce-flat"),
    ("switch.sala_balcao", "Balcão", "mdi:light-recessed"),
    ("switch.sala_de_estar_led_da_escada_switch_1", "Escada", "mdi:led-strip-variant"),
]
TODAS_LUZES = [e for e, _, _ in LUZES_SALA] + [
    "switch.escritorio_teto_switch_1", "switch.escritorio_led_escritorio_switch_1",
    "switch.quintal_lateral", "switch.quintal_fundo"]
LISTA = json.dumps(TODAS_LUZES).replace('"', "'")
N_ACESAS = "expand(" + LISTA + ") | selectattr('state', 'eq', 'on') | list | count"
NET_ON = "(is_state('binary_sensor.rede_cloudflare', 'on') or is_state('binary_sensor.rede_google', 'on'))"
TEMA = "Central escuro"

# circulo colorido atras do icone (o template card do Mushroom 5 nao desenha)
BORDA = "border-radius: 14px !important; border: 1px solid var(--ha-card-border-color, #2a2a2e) !important;"
CIRCULO = ".container { background: color-mix(in srgb, var(--tile-icon-color) 22%, transparent); }"

def fonte(p, s, extra="", info_extra=""):
    # as variaveis vao no proprio ha-tile-info: o .vertical.fixed-info-height do Mushroom sobrescreve as herdadas do ha-card
    lp, ls = round(p * 1.25), round(s * 1.4)
    return ("ha-card { " + BORDA + " %s } ha-tile-info { --ha-tile-info-primary-font-size: %spx; --ha-tile-info-secondary-font-size: %spx;"
            " --ha-tile-info-primary-line-height: %dpx; --ha-tile-info-primary-min-height: %dpx;"
            " --ha-tile-info-secondary-line-height: %dpx; --ha-tile-info-min-height: auto; %s }"
            % (extra, p, s, lp, lp, ls, info_extra))

def mod(css, icone=True):
    st = {".": css}
    if icone:
        st["ha-tile-icon$"] = CIRCULO
    return {"card_mod": {"style": st}}

def titulo(t, icon):
    return {"type": "heading", "heading": t, "icon": icon, "heading_style": "subtitle"}

# ---------- Coluna 1: relogio + agenda ----------
relogio = {
    "type": "custom:mushroom-template-card",
    "primary": "{{ now().strftime('%H:%M') }}",
    "secondary": "{% set d = ['segunda-feira','terça-feira','quarta-feira','quinta-feira','sexta-feira','sábado','domingo'] %}"
                 "{% set m = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'] %}"
                 "{{ d[now().weekday()] | capitalize }}, {{ now().day }} de {{ m[now().month - 1] }}",
    "vertical": True,
    **mod(fonte(78, 17, "background: none; border: none; box-shadow: none; padding: 4px 0 8px;",
                "--ha-tile-info-primary-font-weight: 300; --ha-tile-info-secondary-color: var(--secondary-text-color);"
                " --ha-tile-info-gap: 4px;"), icone=False),
}

AGENDA_MD = (
    "{% set ev = state_attr('sensor.agenda_hoje', 'eventos') or [] %}"
    "{% set ini = as_timestamp(today_at()) %}{% set agora = now().timestamp() %}"
    "{% macro linha(e) %}{% if e.dia_todo %}Dia todo{% else %}**{{ e.ts | timestamp_custom('%H:%M') }}**{% endif %}"
    " &nbsp;{{ e.titulo }} <font color='grey'>· {{ e.agenda }}</font>{% endmacro %}"
    "#### Hoje\n"
    "{% set hoje = (ev | selectattr('ts', 'lt', ini + 86400) | selectattr('te', 'gt', agora) | list) %}"
    "{% for e in hoje[:4] %}{{ linha(e) }}  \n{% else %}Nada mais hoje 🎉\n{% endfor %}"
    "{% if hoje | count > 4 %}<font color='grey'>+{{ hoje | count - 4 }} eventos</font>\n{% endif %}"
    "\n#### Amanhã\n"
    "{% set am = (ev | selectattr('ts', 'lt', ini + 172800) | selectattr('te', 'gt', ini + 86400) | list) %}"
    "{% for e in am[:3] %}{{ linha(e) }}  \n{% else %}Nada marcado\n{% endfor %}"
    "{% if am | count > 3 %}<font color='grey'>+{{ am | count - 3 }} eventos</font>{% endif %}"
)
agenda = {"type": "markdown", "content": AGENDA_MD,
          "card_mod": {"style": "ha-card { " + BORDA + " font-size: 14px; line-height: 1.55; padding: 0 12px 4px; }"
                                "ha-markdown { --markdown-header-font-size: 16px; }"}}

col1 = {"type": "vertical-stack", "cards": [relogio, agenda]}

# ---------- Coluna 2: clima + status da casa ----------
clima = {"type": "weather-forecast", "entity": "weather.casa", "forecast_type": "daily",
         "show_current": True, "show_forecast": True, "forecast_slots": 4,
         "card_mod": {"style": "ha-card { " + BORDA + " }"}}

def status(primary, secondary, icon, color, entity=None, tap=None):
    c = {"type": "custom:mushroom-template-card", "primary": primary, "secondary": secondary,
         "icon": icon, "color": color,
         **mod(fonte(14, 12.5) + " .content { padding: 0 8px !important; gap: 8px !important; }")}
    if entity:
        c["entity"] = entity
        c["tap_action"] = tap or {"action": "more-info"}
    elif tap:
        c["tap_action"] = tap
    return c

st_porta = status(
    "Porta", "{{ 'Aberta' if is_state('" + PORTA + "', 'on') else 'Fechada' }}",
    "{{ 'mdi:door-open' if is_state('" + PORTA + "', 'on') else 'mdi:door-closed' }}",
    "{{ 'red' if is_state('" + PORTA + "', 'on') else 'green' }}", PORTA)
st_internet = status(
    "Internet",
    "{% if " + NET_ON + " %}{{ states('sensor.rede_cloudflare_latencia') | float(0) | round(0) | int }} ms{% else %}Fora do ar{% endif %}",
    "mdi:web", "{{ 'green' if " + NET_ON + " else 'red' }}", "binary_sensor.rede_cloudflare")
st_temp = status(
    "Cozinha",
    "{{ states('sensor.cozinha_casa_temperatura') | float(0) | round(1) }}° · {{ states('sensor.cozinha_casa_umidade') | float(0) | round(0) | int }}%",
    "mdi:thermometer", "orange", "sensor.cozinha_casa_temperatura")
st_luzes = status(
    "Luzes", "{% set n = " + N_ACESAS + " %}{{ 'Apagadas' if n == 0 else n ~ (' acesa' if n == 1 else ' acesas') }}",
    "mdi:lightbulb-group", "{{ 'amber' if (" + N_ACESAS + ") > 0 else 'grey' }}")
st_rubi = status(
    "Rubi", "{{ {'cleaning': 'Limpando', 'docked': 'Na base', 'returning': 'Voltando', 'idle': 'Parado', 'paused': 'Pausado', 'error': 'Erro'}.get(states('vacuum.sala_de_estar_rubi'), states('vacuum.sala_de_estar_rubi')) }}{% set b = states('sensor.sala_de_estar_rubi_bateria') | float(0) | int %}{{ ' · ' ~ b ~ '%' if b < 100 else '' }}",
    "mdi:robot-vacuum", "{{ 'green' if is_state('vacuum.sala_de_estar_rubi', 'cleaning') else 'red' if is_state('vacuum.sala_de_estar_rubi', 'error') else 'teal' }}",
    "vacuum.sala_de_estar_rubi")
st_camera = status("Câmera", "Ver ao vivo", "mdi:cctv", "blue", "camera.sala")

status_grid = {"type": "grid", "columns": 2, "square": False,
               "cards": [st_porta, st_internet, st_temp, st_luzes, st_rubi, st_camera]}

OP = "escritorio_octoprint"
impressora = {"type": "conditional",
              "conditions": [{"condition": "state", "entity": f"binary_sensor.{OP}_printing", "state": "on"}],
              "card": status("Impressora 3D",
                             "{{ states('sensor.OP_job_percentage') | int(0) }}% · termina às {{ as_timestamp(states('sensor.OP_estimated_finish_time'), 0) | timestamp_custom('%H:%M') }}".replace("OP", OP),
                             "mdi:printer-3d-nozzle", "green", f"sensor.{OP}_current_state")}
plex = {"type": "conditional",
        "conditions": [{"condition": "numeric_state", "entity": "sensor.plex_assistindo", "above": 0}],
        "card": status("Plex", "{{ states('sensor.plex_assistindo') }} assistindo", "mdi:plex", "orange", "sensor.plex_assistindo")}

col2 = {"type": "vertical-stack", "cards": [clima, status_grid, impressora, plex]}

# ---------- Coluna 3: luzes da sala + som ----------
def luz(entity, nome, icon):
    return {"type": "custom:mushroom-entity-card", "entity": entity, "name": nome, "icon": icon,
            "icon_color": "amber", "layout": "vertical",
            "tap_action": {"action": "toggle"}, "hold_action": {"action": "more-info"},
            **mod(fonte(13.5, 11.5, "", "--ha-tile-info-gap: 0px;") + " .vertical { padding: 8px 2px !important; }", icone=False)}

luzes = {"type": "grid", "columns": 3, "square": False, "cards": [luz(*l) for l in LUZES_SALA]}
apagar = status("Apagar tudo",
                "{% set n = " + N_ACESAS + " %}{{ 'Nada aceso' if n == 0 else n ~ (' luz acesa' if n == 1 else ' luzes acesas') }}",
                "mdi:lightbulb-off-outline", "red",
                tap={"action": "perform-action", "perform_action": "homeassistant.turn_off",
                     "target": {"entity_id": TODAS_LUZES},
                     "confirmation": {"text": "Apagar todas as luzes da casa?"}})
som = {"type": "custom:mushroom-media-player-card", "entity": "media_player.toda_casa", "name": "Som da casa",
       "use_media_info": True, "show_volume_level": True, "collapsible_controls": True,
       "media_controls": ["play_pause_on", "previous", "next"], "volume_controls": ["volume_set", "volume_mute"],
       "card_mod": {"style": "ha-card { " + BORDA + " }"}}

col3 = {"type": "vertical-stack", "cards": [titulo("Luzes da sala", "mdi:sofa"), luzes, apagar, som]}

view = {"title": "Central", "path": "central", "icon": "mdi:tablet-dashboard", "type": "panel", "theme": TEMA,
        "cards": [{"type": "horizontal-stack", "cards": [col1, col2, col3]}]}
config = {"title": "Central", "views": [view]}

cmds = []
if "--create" in sys.argv:
    cmds.append({"type": "lovelace/dashboards/create", "url_path": "painel-tablet", "title": "Central",
                 "icon": "mdi:tablet-dashboard", "show_in_sidebar": True, "require_admin": False, "mode": "storage"})
cmds.append({"type": "lovelace/config/save", "url_path": "painel-tablet", "config": config})
print(json.dumps(cmds, ensure_ascii=False))
