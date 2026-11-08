# painel_casa.py v3.11 (aba Rede: card do observer no Wi-Fi) - gera os comandos WebSocket do painel "Casa" do Home Assistant (abas por comodo)
# Uso: python3 painel_casa.py [--create] > cmds.json
import json, sys

OP = "escritorio_octoprint"
HALF = {"grid_options": {"columns": 6}}

LUZES = {  # entity: (nome, icone)
    "switch.sala_principal": ("Principal", "mdi:ceiling-light"),
    "switch.sala_atelier": ("Atelier", "mdi:palette"),
    "switch.sala_mesa_de_jantar": ("Mesa de jantar", "mdi:silverware-fork-knife"),
    "switch.sala_lateral": ("Lateral", "mdi:wall-sconce-flat"),
    "switch.sala_balcao": ("Balcão", "mdi:light-recessed"),
    "switch.sala_de_estar_led_da_escada_switch_1": ("LED da escada", "mdi:led-strip-variant"),
    "switch.escritorio_teto_switch_1": ("Teto", "mdi:ceiling-light"),
    "switch.escritorio_led_escritorio_switch_1": ("LED", "mdi:led-strip-variant"),
    "switch.quintal_lateral": ("Lateral", "mdi:outdoor-lamp"),
    "switch.quintal_fundo": ("Fundo", "mdi:outdoor-lamp"),
    "light.lampada": ("Lâmpada RGB", "mdi:lightbulb"),
}
LISTA_LUZES = json.dumps(list(LUZES)).replace('"', "'")

def heading(t, icon):
    return {"type": "heading", "heading": t, "icon": icon}

def tpl(primary, secondary, icon, color, half=True, **kw):
    c = {"type": "custom:mushroom-template-card", "primary": primary,
         "secondary": secondary, "icon": icon, "color": color, **kw}
    if half:
        c.update(HALF)
    return c

def tile(entity, name=None, icon=None, color=None, cols=6, **kw):
    c = {"type": "tile", "entity": entity, "grid_options": {"columns": cols}, **kw}
    if name: c["name"] = name
    if icon: c["icon"] = icon
    if color: c["color"] = color
    return c

def luz(entity, cols=6):
    nome, icon = LUZES[entity]
    return tile(entity, nome, icon, "amber", cols, tap_action={"action": "toggle"},
                icon_tap_action={"action": "toggle"})

def cena(entity, nome, icon, cols=6, color="indigo"):
    act = {"action": "perform-action", "perform_action": "scene.turn_on", "target": {"entity_id": entity}}
    return tile(entity, nome, icon, color, cols, tap_action=act, icon_tap_action=act, hide_state=True)

def graf(nome, icon, ents, horas=6, pph=12):
    return {"type": "custom:mini-graph-card", "name": nome, "icon": icon,
            "hours_to_show": horas, "points_per_hour": pph, "line_width": 2, "smoothing": True,
            "show": {"legend": True, "labels": False, "fill": "fade"}, "entities": ents}

def sec(*cards):
    return {"type": "grid", "cards": list(cards)}

camera_sala = {"type": "picture-entity", "entity": "camera.sala", "camera_view": "live",
               "show_name": False, "show_state": False, "tap_action": {"action": "more-info"},
               "grid_options": {"columns": 12}}

# ---------- Plex ----------
PLEX_LIBS = ["filmes", "filmes_007", "animacoes", "hbo", "fox", "appletv", "paramount", "prime", "desenhos", "musica"]
PLEX_LISTA = "['" + "','".join("sensor.plex_" + l for l in PLEX_LIBS) + "']"
plex_sessoes = ("{% set a = states.sensor.plex_assistindo.attributes %}"
                "{% for k, v in a.items() if k not in ['unit_of_measurement', 'friendly_name', 'icon'] %}"
                "{{ v }} ({{ k }}){{ ' · ' if not loop.last }}{% endfor %}")
plex_status = tpl(
    "Plex",
    "{% set n = states('sensor.plex_assistindo') | int(0) %}{% if n == 0 %}Ninguém assistindo{% else %}" + plex_sessoes + "{% endif %}",
    "mdi:plex",
    "{{ 'orange' if states('sensor.plex_assistindo') | int(0) > 0 else 'grey' }}",
    half=False, entity="sensor.plex_assistindo", tap_action={"action": "url", "url_path": "https://app.plex.tv/desktop"},
    badge_icon="{{ 'mdi:update' if is_state('update.plex', 'on') }}", badge_color="blue")
plex_ultimo = tpl(
    "Último adicionado",
    "{% set l = expand(LISTA) | selectattr('attributes.last_added_timestamp', 'defined') | sort(attribute='attributes.last_added_timestamp', reverse=true) | list %}"
    "{% if l %}{{ l[0].attributes.last_added_item }} · {{ as_timestamp(l[0].attributes.last_added_timestamp) | timestamp_custom('%d/%m/%Y') }}{% endif %}".replace("LISTA", PLEX_LISTA),
    "mdi:new-box", "blue", half=False)
plex_biblioteca = {"type": "markdown", "content": (
    "| Biblioteca | Conteúdo |\n|---|---|\n"
    "{% for id in LISTA %}{% set e = expand(id) | first %}{% set a = e.attributes %}"
    "| {{ a.friendly_name | replace('Atlas ', '') }} | "
    "{% if a.artists is defined %}{{ a.artists }} artistas · {{ a.albums }} álbuns · {{ e.state }} faixas"
    "{% elif a.shows is defined %}{{ a.shows }} série{{ 's' if a.shows != 1 }} · {{ e.state }} episódios"
    "{% else %}{{ e.state }} filme{{ 's' if e.state | int(0) != 1 }}{% endif %} |\n{% endfor %}").replace("LISTA", PLEX_LISTA)}
plex = [heading("Plex", "mdi:plex"), plex_status, plex_ultimo, plex_biblioteca]
plex_casa = {"type": "conditional",
             "conditions": [{"condition": "numeric_state", "entity": "sensor.plex_assistindo", "above": 0}],
             "card": plex_status}

agenda = {"type": "calendar", "initial_view": "listWeek",
          "entities": ["calendar.pessoal", "calendar.familia", "calendar.birthdays",
                       "calendar.feriados_no_brasil", "calendar.f1"],
          "grid_options": {"columns": 12}}

# ---------- Casa (resumo) ----------
saudacao = tpl(
    "{% set h = now().hour %}{{ 'Bom dia' if 5 <= h < 12 else 'Boa tarde' if 12 <= h < 18 else 'Boa noite' }}, {{ user }}",
    "{% set d = ['segunda','terça','quarta','quinta','sexta','sábado','domingo'] %}{{ d[now().weekday()] | capitalize }}, {{ now().strftime('%d/%m') }}",
    "mdi:home", "amber", half=False,
)

luzes_acesas = "{{ expand(LISTA) | selectattr('state', 'eq', 'on') | list | count }}".replace("LISTA", LISTA_LUZES)

chips = {
    "type": "custom:mushroom-chips-card",
    "chips": [
        {"type": "weather", "entity": "weather.casa", "show_conditions": True, "show_temperature": True},
        {"type": "template", "icon": "mdi:lightbulb-group",
         "content": "{% set n = " + luzes_acesas[3:-3] + " %}{{ n }} luz{{ 'es' if n != 1 }} acesa{{ 's' if n != 1 }}",
         "icon_color": "{{ 'amber' if (" + luzes_acesas[3:-3] + ") > 0 else 'disabled' }}",
         "tap_action": {"action": "navigate", "navigation_path": "/painel-casa/sala"}},
        {"type": "template", "icon": "{{ 'mdi:door-open' if is_state('binary_sensor.entrada_porta_de_entrada_porta', 'on') else 'mdi:door-closed' }}",
         "content": "Porta {{ 'aberta' if is_state('binary_sensor.entrada_porta_de_entrada_porta', 'on') else 'fechada' }}",
         "icon_color": "{{ 'red' if is_state('binary_sensor.entrada_porta_de_entrada_porta', 'on') else 'green' }}",
         "entity": "binary_sensor.entrada_porta_de_entrada_porta", "tap_action": {"action": "more-info"}},
        {"type": "template", "icon": "mdi:thermometer",
         "content": "{{ states('sensor.cozinha_casa_temperatura') | round(1) }}°C · {{ states('sensor.cozinha_casa_umidade') | round(0) }}%",
         "icon_color": "orange", "entity": "sensor.cozinha_casa_temperatura", "tap_action": {"action": "more-info"}},
        {"type": "template", "icon": "mdi:flash",
         "content": "R$ {{ '%.2f' | format(states('sensor.custo_setup_hoje') | float(0)) | replace('.', ',') }} hoje",
         "icon_color": "yellow", "tap_action": {"action": "navigate", "navigation_path": "/painel-casa/escritorio"}},
    ],
}

clima = {"type": "weather-forecast", "entity": "weather.casa", "forecast_type": "daily", "show_current": True, "show_forecast": True}

desligar_tudo = tpl("Apagar tudo", "{% set n = " + luzes_acesas[3:-3] + " %}{{ 'Tudo apagado' if n == 0 else n ~ (' luz acesa' if n == 1 else ' luzes acesas') }}", "mdi:lightbulb-off-outline", "red",
                    half=False,
                    tap_action={"action": "perform-action", "perform_action": "homeassistant.turn_off",
                                "target": {"entity_id": [e for e in LUZES if e != "light.lampada"]},
                                "confirmation": {"text": "Apagar todas as luzes da casa?"}})

aspirador = tile("vacuum.sala_de_estar_rubi", "Rubi", "mdi:robot-vacuum", "teal", 12,
                 features=[{"type": "vacuum-commands", "commands": ["start_pause", "stop", "return_home", "locate"]}],
                 features_position="bottom")

# Impressora
imp_status = tpl(
    "Impressora 3D",
    "{% set s = states('sensor.OP_current_state') %}{% set p = states('binary_sensor.OP_printing') %}"
    "{% if p == 'on' %}{{ states('sensor.OP_job_percentage') | int(0) }}% · termina às "
    "{{ as_timestamp(states('sensor.OP_estimated_finish_time'), 0) | timestamp_custom('%H:%M') }}"
    "{% elif s in ['unavailable', 'unknown'] %}Desconectada{% else %}{{ {'operational': 'Pronta', 'printing': 'Imprimindo', 'paused': 'Pausada', 'pausing': 'Pausando', 'cancelling': 'Cancelando', 'error': 'Erro', 'offline': 'Offline', 'finishing': 'Finalizando'}.get(s | lower, s) }}{% endif %}".replace("OP", OP),
    "mdi:printer-3d-nozzle",
    "{% set p = states('binary_sensor.OP_printing') %}{{ 'green' if p == 'on' else 'blue' if p == 'off' else 'disabled' }}".replace("OP", OP),
    half=False, entity=f"sensor.{OP}_current_state",
    badge_icon="{{ 'mdi:alert' if is_state('binary_sensor.OP_printing_error', 'on') }}".replace("OP", OP),
    badge_color="red", tap_action={"action": "more-info"},
)
imprimindo = [{"condition": "state", "entity": f"binary_sensor.{OP}_printing", "state": "on"}]
imp_arquivo = {"type": "conditional", "conditions": imprimindo,
               "card": tpl("{{ states('sensor.OP_current_file') }}".replace("OP", OP),
                           "Começou às {{ as_timestamp(states('sensor.OP_start_time'), 0) | timestamp_custom('%H:%M') }}".replace("OP", OP),
                           "mdi:file-cad-box", "grey", half=False)}

def botao(nome, icon, entity, color):
    return tpl(nome, "", icon, color, half=False, entity=f"button.{OP}_{entity}",
               tap_action={"action": "perform-action", "perform_action": "button.press",
                           "target": {"entity_id": f"button.{OP}_{entity}"},
                           "confirmation": {"text": f"{nome} a impressão?"}})

imp_botoes = {"type": "conditional", "conditions": imprimindo,
              "card": {"type": "grid", "columns": 3, "square": False, "cards": [
                  botao("Pausar", "mdi:pause", "pause_job", "orange"),
                  botao("Retomar", "mdi:play", "resume_job", "green"),
                  botao("Parar", "mdi:stop", "stop_job", "red")]}}

def som(entity):
    return {"type": "custom:mushroom-media-player-card", "entity": entity, "use_media_info": True,
            "show_volume_level": True, "collapsible_controls": True,
            "media_controls": ["play_pause_on", "previous", "next"],
            "volume_controls": ["volume_set", "volume_mute"]}

view_casa = {
    "title": "Casa", "path": "casa", "icon": "mdi:home", "type": "sections", "max_columns": 3,
    "sections": [
        sec(saudacao, chips, plex_casa, camera_sala),
        sec(heading("Agora", "mdi:home-lightning-bolt"), desligar_tudo, aspirador,
            tile("binary_sensor.entrada_porta_de_entrada_porta", "Porta de entrada", color="red"),
            tile("binary_sensor.sala_de_estar_sensor_escada_movimento", "Movimento escada", color="purple"),
            heading("Impressora 3D", "mdi:printer-3d"), imp_status, imp_arquivo, imp_botoes,
            heading("Som", "mdi:speaker"), som("media_player.toda_casa"), som("media_player.relogio_suite"), som("media_player.som_atelier")),
        sec(heading("Clima", "mdi:weather-partly-cloudy"), clima,
            heading("Agenda", "mdi:calendar-month"), agenda),
    ],
}

# ---------- Sala ----------
view_sala = {
    "title": "Sala", "path": "sala", "icon": "mdi:sofa", "type": "sections", "max_columns": 3,
    "sections": [
        sec(heading("Câmera", "mdi:cctv"), camera_sala,
            heading("Ambiente", "mdi:home-thermometer"),
            graf("Cozinha", "mdi:thermometer", [
                {"entity": "sensor.cozinha_casa_temperatura", "name": "Temperatura", "color": "#f2994a"},
                {"entity": "sensor.cozinha_casa_umidade", "name": "Umidade", "color": "#4f8bf7", "y_axis": "secondary"}], 24),
            tile("binary_sensor.sala_de_estar_sensor_escada_movimento", "Movimento escada", color="purple", cols=12)),
        sec(heading("Luzes", "mdi:lightbulb-group"),
            luz("switch.sala_principal"), luz("switch.sala_atelier"), luz("switch.sala_mesa_de_jantar"),
            luz("switch.sala_lateral"), luz("switch.sala_balcao"), luz("switch.sala_de_estar_led_da_escada_switch_1"),
            luz("light.lampada", cols=12),
            tile("switch.sala_tomada_balcao", "Tomada do balcão", "mdi:power-socket-de", "blue", 12,
                 tap_action={"action": "toggle"}, icon_tap_action={"action": "toggle"}),
            heading("Controle", "mdi:remote"),
            cena("scene.volume_2", "Volume +", "mdi:volume-plus"), cena("scene.volume", "Volume -", "mdi:volume-minus"),
            cena("scene.on_off_bluray", "Blu-ray liga/desliga", "mdi:disc-player"), cena("scene.ejetar_blu_ray", "Ejetar Blu-ray", "mdi:eject"),
            cena("scene.liga_teto", "Liga teto", "mdi:ceiling-fan-light", color="amber"),
            cena("scene.desliga_teto", "Desliga teto", "mdi:ceiling-fan", color="grey"),
            cena("scene.desliga_sala", "Desliga sala", "mdi:lightbulb-group-off", cols=12, color="red")),
        sec(heading("Rubi", "mdi:robot-vacuum"), aspirador,
            tile("select.sala_de_estar_rubi_modo", "Modo", "mdi:map-marker-path", "teal", 12,
                 features=[{"type": "select-options"}]),
            tile("sensor.sala_de_estar_rubi_bateria", "Bateria", cols=6),
            tile("sensor.sala_de_estar_rubi_area_de_limpeza", "Última área", "mdi:texture-box", cols=6),
            tile("sensor.sala_de_estar_rubi_tempo_de_limpeza", "Último tempo", "mdi:timer-outline", cols=6),
            tile("switch.sala_de_estar_rubi_nao_perturbe", "Não perturbe", "mdi:sleep", "indigo", 6)),
    ],
}

historico_graf = {"type": "statistics-graph", "title": "Consumo por mês (kWh)", "chart_type": "bar",
                  "period": "month", "stat_types": ["change"], "days_to_show": 1110, "hide_legend": False,
                  "entities": [{"entity": "tuya:setup_escritorio_historico", "name": "Histórico (app)"},
                               {"entity": "sensor.setup_escritorio_energia", "name": "Medido pelo HA"}],
                  "grid_options": {"columns": 12, "rows": 5}}
historico_anos = {"type": "markdown", "content": """**Por ano** (custo estimado com o preço atual do kWh)

| Ano | Consumo | Custo |
|---|---|---|
| 2023 | 45,25 kWh | R$ 46 |
| 2024 | 251,91 kWh | R$ 255 |
| 2025 | 586,12 kWh | R$ 594 |
| 2026 | 457,91 kWh | R$ 464 |

Nov/2023 a dez/2023 são só 2 meses. 2026 vai até 06/11; daí em diante o HA mede."""}

setup_cards = [
    heading("Setup (tomada da mesa)", "mdi:power-socket-de"),
    tile("switch.escritorio_mesa_tomada", "Tomada da mesa", "mdi:power-socket-de", "blue", 12,
         tap_action={"action": "more-info"},
         icon_tap_action={"action": "toggle", "confirmation": {"text": "Ligar/desligar TODO o setup do escritório?"}}),
    tile("sensor.escritorio_mesa_potencia", "Potência agora", "mdi:flash", cols=6),
    tile("sensor.setup_escritorio_hoje", "Consumo hoje", "mdi:counter", cols=6),
    tile("sensor.custo_setup_hoje", "Custo hoje", "mdi:cash", cols=6),
    tile("sensor.custo_setup_mes", "Custo no mês", "mdi:cash-multiple", cols=6),
    graf("Potência", "mdi:flash", [{"entity": "sensor.escritorio_mesa_potencia", "name": "W", "color": "#f2c94c"}], 24),
    tile("input_number.preco_do_kwh", "Preço do kWh", "mdi:cash-edit", cols=12),
]

stacklog = [
    heading("Stacklog", "mdi:format-list-checks"),
    tpl("Stacklog",
        "{{ states('sensor.stacklog_abertas') }} abertas · {{ states('sensor.stacklog_projetos_ativos') }} projetos ativos{% set o = states('sensor.stacklog_observacoes') | int(0) %}{{ ' · ' ~ o ~ ' com observação' if o > 0 }}",
        "mdi:format-list-checks", "cyan", half=False,
        tap_action={"action": "url", "url_path": "https://stacklog.example.com"}),
    tile("sensor.stacklog_concluidas_hoje", "Concluídas hoje", "mdi:check-circle-outline", "green", 6),
    tile("sensor.stacklog_concluidas_7_dias", "Últimos 7 dias", "mdi:calendar-check", "green", 6),
    tpl("Última concluída", "{{ states('sensor.stacklog_ultima_concluida') }}", "mdi:check-decagram", "green",
        half=False, multiline_secondary=True, entity="sensor.stacklog_ultima_concluida", tap_action={"action": "more-info"}),
]

# ---------- Escritorio ----------
view_escritorio = {
    "title": "Escritório", "path": "escritorio", "icon": "mdi:desk", "type": "sections", "max_columns": 2,
    "sections": [
        sec(heading("Luzes", "mdi:lightbulb-group"),
            luz("switch.escritorio_teto_switch_1"), luz("switch.escritorio_led_escritorio_switch_1"),
            *setup_cards,
            heading("Impressora 3D", "mdi:printer-3d"), imp_status, imp_arquivo, imp_botoes),
        sec(heading("Histórico de consumo", "mdi:chart-bar"), historico_graf, historico_anos, *stacklog),
    ],
}

# ---------- Externo ----------
view_externo = {
    "title": "Externo", "path": "externo", "icon": "mdi:pine-tree", "type": "sections", "max_columns": 2,
    "sections": [
        sec(heading("Quintal", "mdi:outdoor-lamp"), luz("switch.quintal_lateral"), luz("switch.quintal_fundo"),
            heading("Entrada", "mdi:door"),
            tile("binary_sensor.entrada_porta_de_entrada_porta", "Porta de entrada", color="red", cols=12),
            tile("sensor.entrada_porta_de_entrada_bateria", "Bateria do sensor", cols=12)),
        sec(heading("Clima", "mdi:weather-partly-cloudy"), clima),
    ],
}

# ---------- Servidores ----------
def servidor(p, disco_nome, iface, extras):
    return [
        graf("CPU e temperatura", "mdi:cpu-64-bit", [
            {"entity": f"sensor.{p}_cpu", "name": "CPU", "color": "#4f8bf7"},
            {"entity": f"sensor.{p}_temperatura", "name": "Temperatura", "color": "#f2994a", "y_axis": "secondary"}]),
        tpl("Memória",
            "{{ states('sensor.P_memoria') }}% · {{ (states('sensor.P_memoria_livre') | float(0) / 1024) | round(1) }} GiB livres".replace("P_", p + "_"),
            "mdi:memory",
            "{% set x = states('sensor.P_memoria') | float(0) %}{{ 'red' if x > 85 else 'orange' if x > 70 else 'green' }}".replace("P_", p + "_"),
            entity=f"sensor.{p}_memoria", tap_action={"action": "more-info"}),
        tpl(disco_nome,
            "{{ states('sensor.P_disco') }}% · {{ states('sensor.P_disco_livre') | round(0) }} GiB livres".replace("P_", p + "_"),
            "mdi:harddisk",
            "{% set x = states('sensor.P_disco') | float(0) %}{{ 'red' if x > 90 else 'orange' if x > 80 else 'blue' }}".replace("P_", p + "_"),
            entity=f"sensor.{p}_disco", tap_action={"action": "more-info"}),
        *extras,
        tpl("Ligado há",
            "{% set d = now() - as_datetime(states('sensor.P_ligado_desde')) %}{{ d.days }} dia{{ 's' if d.days != 1 }} e {{ (d.seconds // 3600) }} h".replace("P_", p + "_"),
            "mdi:timer-outline", "teal", entity=f"sensor.{p}_ligado_desde", tap_action={"action": "more-info"}),
        graf(f"Rede ({iface})", "mdi:swap-vertical", [
            {"entity": f"sensor.{p}_rede_download", "name": "Download", "color": "#27ae60"},
            {"entity": f"sensor.{p}_rede_upload", "name": "Upload", "color": "#9b51e0"}]),
    ]

atlas_extras = [tpl("Disco 4 TB",
                    "{{ states('sensor.atlas_4tb') }}% · {{ (states('sensor.atlas_4tb_livre') | float(0) / 1024) | round(2) }} TiB livres",
                    "mdi:harddisk-plus",
                    "{% set x = states('sensor.atlas_4tb') | float(0) %}{{ 'red' if x > 90 else 'orange' if x > 80 else 'blue' }}",
                    entity="sensor.atlas_4tb", tap_action={"action": "more-info"}),
                tpl("Carga", "{{ states('sensor.atlas_load') }} (média 5 min)", "mdi:speedometer", "purple",
                    entity="sensor.atlas_load", tap_action={"action": "more-info"})]
boreas_extras = [
    tpl("Containers", "{{ states('sensor.boreas_containers') }} rodando", "mdi:docker", "blue",
        entity="sensor.boreas_containers", tap_action={"action": "more-info"}),
    tpl("Tailscale",
        "↓ {{ states('sensor.boreas_tailscale_download') | float(0) | round(2) }} · ↑ {{ states('sensor.boreas_tailscale_upload') | float(0) | round(2) }} Mbit/s",
        "mdi:vpn",
        "{{ 'green' if (states('sensor.boreas_tailscale_download') | float(0) + states('sensor.boreas_tailscale_upload') | float(0)) > 0.05 else 'grey' }}",
        half=False, entity="sensor.boreas_tailscale_download", tap_action={"action": "more-info"}),
]
pihole = [
    heading("Pi-hole", "mdi:pi-hole"),
    tpl("Pi-hole",
        "{% if is_state('switch.pihole', 'on') %}{{ states('sensor.pihole_bloqueados') }} bloqueados · {{ states('sensor.pihole_percentual') | float(0) | round(1) }}% das consultas{% else %}Bloqueio DESLIGADO{% endif %}",
        "mdi:shield-check",
        "{{ 'green' if is_state('switch.pihole', 'on') else 'red' }}",
        half=False, entity="switch.pihole", tap_action={"action": "more-info"},
        badge_icon="{{ 'mdi:update' if is_state('update.escritorio_pi_hole_atualizacao_ftl_disponivel', 'on') or is_state('update.escritorio_pi_hole_atualizacao_do_core_disponivel', 'on') or is_state('update.escritorio_pi_hole_atualizacao_da_web_disponivel', 'on') }}",
        badge_color="blue"),
    tile("sensor.pihole_consultas", "Consultas hoje", "mdi:dns", cols=6),
    tile("sensor.pihole_clientes", "Clientes", "mdi:devices", cols=6),
    tile("switch.pihole", "Bloqueio", "mdi:shield", "green", 6,
         tap_action={"action": "toggle"}, icon_tap_action={"action": "toggle"}),
    tpl("Pausar 5 min", "Libera tudo por 5 minutos", "mdi:timer-pause-outline", "orange",
        tap_action={"action": "perform-action", "perform_action": "pi_hole.disable",
                    "target": {"entity_id": "switch.pihole"}, "data": {"duration": "00:05:00"}}),
    graf("Bloqueio (%)", "mdi:chart-line", [{"entity": "sensor.pihole_percentual", "name": "% bloqueado", "color": "#e74c3c"}], 24),
]
transmission = [
    heading("Transmission", "mdi:download-network"),
    tpl("Transmission",
        "{{ states('sensor.transmission_ativos') }} ativo(s) de {{ states('sensor.transmission_total') }} · ↓ {{ states('sensor.transmission_download') }} ↑ {{ states('sensor.transmission_upload') }} MB/s",
        "mdi:download-network",
        "{{ 'green' if states('sensor.transmission_ativos') | int(0) > 0 else 'grey' }}",
        half=False, entity="sensor.transmission_status", tap_action={"action": "more-info"}),
    tile("switch.transmission", "Torrents ligados", "mdi:play-pause", "green", 6,
         tap_action={"action": "toggle"}, icon_tap_action={"action": "toggle"}),
    tile("switch.transmission_tartaruga", "Modo tartaruga", "mdi:tortoise", "teal", 6,
         tap_action={"action": "toggle"}, icon_tap_action={"action": "toggle"}),
    tile("sensor.transmission_espaco", "Espaço livre", "mdi:harddisk", cols=12),
    graf("Velocidade", "mdi:speedometer", [
        {"entity": "sensor.transmission_download", "name": "Download", "color": "#27ae60"},
        {"entity": "sensor.transmission_upload", "name": "Upload", "color": "#9b51e0"}]),
]

traefik = [
    heading("Traefik", "mdi:router-network"),
    tpl("Traefik",
        "{% if is_state('binary_sensor.traefik_online', 'on') %}{{ states('sensor.traefik_rotas') }} rotas · {{ states('sensor.traefik_servicos') }} serviços · {% set n = states('sensor.traefik_problemas') | int(0) %}{{ 'sem problemas' if n == 0 else n ~ ' problema(s)' }}{% else %}FORA DO AR{% endif %}",
        "mdi:router-network",
        "{{ 'red' if not is_state('binary_sensor.traefik_online', 'on') else 'orange' if states('sensor.traefik_problemas') | int(0) > 0 else 'green' }}",
        half=False, entity="binary_sensor.traefik_online",
        tap_action={"action": "url", "url_path": "https://traefik.example.com/dashboard/"}),
    tpl("Certificado *.example.com",
        "{% set d = (as_datetime(states('sensor.traefik_certificado')) - now()).days %}vence em {{ d }} dias ({{ as_timestamp(states('sensor.traefik_certificado')) | timestamp_custom('%d/%m/%Y') }})",
        "mdi:certificate",
        "{% set d = (as_datetime(states('sensor.traefik_certificado')) - now()).days %}{{ 'green' if d > 25 else 'orange' if d > 10 else 'red' }}",
        half=False, entity="sensor.traefik_certificado", tap_action={"action": "more-info"}),
]

view_servidores = {
    "title": "Servidores", "path": "servidores", "icon": "mdi:server", "type": "sections", "max_columns": 3,
    "sections": [
        sec(heading("Atlas", "mdi:server"), *servidor("atlas", "Disco /DATA", "eth0", atlas_extras), *traefik),
        sec(heading("Boreas", "mdi:server-network"), *servidor("boreas", "Disco", "enp2s0", boreas_extras), *transmission),
        sec(*pihole, *plex),
    ],
}

# ---------- Mesh (MeshCore) ----------
def dias(e):
    return ("{% set d = states('E') | float(0) %}{% if d < 1 %}{{ (d * 24) | round(0) | int }} h"
            "{% else %}{{ d | round(0) | int }} days{% endif %}").replace("E", e)

mesh_companion = [
    heading("Casa-Companion (companion)", "mdi:radio-handheld"),
    tpl("Casa-Companion",
        "{% if is_state('sensor.mesh_status', 'online') %}Online · battery {{ states('sensor.mesh_bateria') | float(0) | round(0) }}% · "
        "{{ states('sensor.mesh_temperatura') | float(0) | round(0) }} °C · up for UPTIME{% else %}OFFLINE{% endif %}".replace("UPTIME", dias("sensor.mesh_uptime")),
        "mdi:radio-handheld",
        "{{ 'green' if is_state('sensor.mesh_status', 'online') else 'red' }}",
        half=False, entity="sensor.mesh_status",
        badge_icon="{{ 'mdi:update' if is_state('update.mesh_firmware', 'on') }}", badge_color="blue"),
    tpl("Radio",
        "{{ states('sensor.mesh_frequencia') }} MHz · BW {{ states('sensor.mesh_banda') }} · SF{{ states('sensor.mesh_sf') }} · {{ states('sensor.mesh_potencia') }} dBm",
        "mdi:sine-wave", "blue", half=False),
    tile("sensor.mesh_rssi", "RSSI", "mdi:signal", "teal"),
    tile("sensor.mesh_snr", "SNR", "mdi:signal-variant", "teal"),
    tile("sensor.mesh_ruido", "Noise floor", "mdi:waveform", "grey"),
    tile("sensor.mesh_bateria", "Battery", "mdi:battery", "green"),
    tile("sensor.mesh_enviadas", "Sent", "mdi:send", "indigo"),
    tile("sensor.mesh_recebidas", "Received", "mdi:inbox-arrow-down", "indigo"),
    graf("Signal", "mdi:signal", [
        {"entity": "sensor.mesh_rssi", "name": "RSSI", "color": "#2d9cdb"},
        {"entity": "sensor.mesh_snr", "name": "SNR", "color": "#27ae60", "y_axis": "secondary"}], horas=24),
]

mesh_repetidor = [
    heading("REP-CASA-4387 (repeater)", "mdi:radio-tower"),
    tpl("REP-CASA-4387",
        "{% if is_state('binary_sensor.repetidor_online', 'on') %}Online · battery {{ states('sensor.repetidor_bateria') | float(0) | round(0) }}% · "
        "{{ states('sensor.repetidor_temperatura') | float(0) | round(0) }} °C · up for UPTIME{% else %}OFFLINE{% endif %}".replace("UPTIME", dias("sensor.repetidor_uptime")),
        "mdi:radio-tower",
        "{{ 'green' if is_state('binary_sensor.repetidor_online', 'on') else 'red' }}",
        half=False, entity="binary_sensor.repetidor_online",
        badge_icon="{{ 'mdi:update' if is_state('update.repetidor_firmware', 'on') }}", badge_color="blue"),
    tpl("Firmware",
        "{% set a = states.update.repetidor_firmware.attributes %}{{ a.reported_version }}"
        "{% if is_state('update.repetidor_firmware', 'on') %} · {{ a.latest_version }} available{% endif %}",
        "mdi:chip", "{{ 'blue' if is_state('update.repetidor_firmware', 'on') else 'grey' }}",
        half=False, entity="update.repetidor_firmware", tap_action={"action": "more-info"}),
    tpl("Observer upload (CoreScope)",
        "last packet {% set t = states('sensor.corescope_meu_observer_ultimo_pacote') %}{% if t not in ['unknown', 'unavailable', 'none', ''] %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) %}{{ (h * 60) | int ~ ' min' if h < 1 else (h | int ~ ' h' if h < 48 else (h / 24) | int ~ ' days') }} ago{% else %}never{% endif %} · {{ states('sensor.corescope_meu_observer') }} pkts/h · online {% set t = states('sensor.corescope_meu_observer_visto') %}{% if t not in ['unknown', 'unavailable', 'none', ''] %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) %}{{ (h * 60) | int ~ ' min' if h < 1 else (h | int ~ ' h' if h < 48 else (h / 24) | int ~ ' days') }} ago{% else %}never{% endif %}",
        "mdi:antenna",
        "{% set t = states('sensor.corescope_meu_observer_ultimo_pacote') %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) if t not in ['unknown', 'unavailable', 'none', ''] else 999 %}{{ 'green' if h < 1 else 'orange' if h < 24 else 'red' }}",
        half=False, entity="sensor.corescope_meu_observer", tap_action={"action": "url", "url_path": "https://corescope.example.org/"}),
    tile("sensor.repetidor_vizinhos", "Neighbors", "mdi:account-group", "purple"),
    tile("sensor.repetidor_ruido", "Noise floor", "mdi:waveform", "grey"),
    tile("sensor.repetidor_enviadas", "Sent", "mdi:send", "indigo"),
    tile("sensor.repetidor_recebidas", "Received", "mdi:inbox-arrow-down", "indigo"),
    tile("sensor.repetidor_erros", "Receive errors", "mdi:alert-circle-outline", "orange"),
    tile("sensor.repetidor_dup_flood", "Flood duplicates", "mdi:content-duplicate", "grey"),
    graf("Battery and temperature", "mdi:battery-heart-variant", [
        {"entity": "sensor.repetidor_bateria_v", "name": "Battery (V)", "color": "#27ae60"},
        {"entity": "sensor.repetidor_temperatura", "name": "Temperature", "color": "#eb5757", "y_axis": "secondary"}], horas=48),
]

mesh_enviar = {"type": "custom:mushroom-template-card", "primary": "Send", "icon": "mdi:send",
               "color": "blue", "grid_options": {"columns": 12},
               "tap_action": {"action": "perform-action", "perform_action": "meshcore.send_ui_message", "data": {},
                              "confirmation": {"text": "Send this message to the mesh?"}}}
mesh_lista = {"type": "markdown", "content": (
    "{% set l = state_attr('sensor.mesh_ultima_mensagem', 'mensagens') or [] %}"
    "{% if not l %}_No messages since setup. New ones will show up here._{% else %}"
    "| Time | From | Channel | Message |\n|---|---|---|---|\n"
    "{% for m in l %}| {{ m.hora }} | {{ '➜ ' if m.saida }}{{ m.de }} | {{ 'Direct' if m.canal == 'Direta' else m.canal }} | {{ m.msg | replace('|', '/') }} |\n{% endfor %}{% endif %}")}

mesh_public = {"type": "markdown", "content": (
    "{% set l = state_attr('sensor.corescope_canal_public', 'messages') or [] %}"
    "{% if not l %}_No data from CoreScope._{% else %}"
    "| Time | From | Message | Hops |\n|---|---|---|---|\n"
    "{% for m in l | reverse %}| {{ as_timestamp(m.timestamp) | timestamp_custom('%d/%m %H:%M') }} "
    "| {{ (m.sender or '?') | replace('|', '/') }} | {{ (m.text or '') | replace('|', '/') | replace('\\n', ' ') }} | {{ m.hops }} |\n{% endfor %}"
    "\n<sub>{{ state_attr('sensor.corescope_canal_public', 'total') }} messages captured · corescope.example.org · every 2 min</sub>{% endif %}")}

mesh_mensagens = [
    heading("Messages", "mdi:message-text"),
    {"type": "entities", "entities": [
        {"entity": "select.meshcore_recipient_type", "name": "Send to"},
        {"entity": "select.meshcore_channel", "name": "Channel"},
        {"entity": "select.meshcore_contact", "name": "Contact"},
        {"entity": "text.meshcore_message", "name": "Message"}]},
    mesh_enviar,
    heading("Latest messages", "mdi:history"),
    mesh_lista,
    heading("Public channel · whole network (CoreScope)", "mdi:forum"),
    mesh_public,
]

# ---------- CoreScope (comunidade) ----------
def cs_idade(attr):
    # horas desde o atributo (ISO UTC) -> texto curto
    return ("{% set t = state_attr('E', 'A') %}{% if t %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) %}"
            "{{ (h * 60) | int ~ ' min' if h < 1 else (h | int ~ ' h' if h < 48 else (h / 24) | int ~ ' days') }}{% else %}never{% endif %}").replace("A", attr)

def cs_cor(e):
    return ("{% set t = state_attr('E', 'last_relayed') %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) if t else 999 %}"
            "{{ 'green' if h < 3 else 'orange' if h < 24 else 'red' }}").replace("E", e)

def cs_no(e, nome, half=False):
    sec_ = ("{{ states('E') }} relays/24h · {{ state_attr('E', 'relay_count_1h') }}/1h · grade {{ state_attr('E', 'usefulness_grade') }}"
            " · last relay " + cs_idade("last_relayed") + " ago").replace("E", e)
    return tpl(nome, sec_, "mdi:radio-tower", cs_cor(e), half=half, entity=e,
               tap_action={"action": "url", "url_path": "https://corescope.example.org/"})

def cs_relogio(slug):
    e = "sensor.corescope_" + slug + "_relogio"
    return ("{% set m = states('E') | int(0) %}{% set s = state_attr('E', 'severity') %}"
            "{% if s == 'ok' %}correct{% elif s == 'no_clock' %}never set{% elif s == 'bimodal_clock' %}unstable{% else %}{{ s }}{% endif %}"
            "{% if m | abs >= 5 %} · {{ 'behind' if m < 0 else 'ahead' }} {{ (m | abs / 60) | round(1) if m | abs >= 60 else m | abs }}{{ ' h' if m | abs >= 60 else ' min' }}{% endif %}").replace("E", e)

def cs_disp_cor(slug):
    return ("{% set d = states('sensor.corescope_" + slug + "_disponibilidade') | float(0) %}"
            "{{ 'green' if d >= 90 else 'orange' if d >= 50 else 'red' }}")

D_AMIGO = "sensor.corescope_amigo_disponibilidade"
cs_amigo_extra = [
    tpl("Availability (7 days)", "{{ states('" + D_AMIGO + "') }}% of hours with traffic", "mdi:percent-circle", cs_disp_cor("amigo")),
    tpl("Signal", "grade {{ state_attr('" + D_AMIGO + "', 'signalGrade') }} · mean SNR {{ state_attr('" + D_AMIGO + "', 'snrMean') }} dB", "mdi:signal", "teal"),
    tpl("Packets per day", "{{ state_attr('" + D_AMIGO + "', 'avgPacketsPerDay') }} on average (7 days)", "mdi:chart-bar", "indigo"),
    tpl("Longest silence", "{{ ((state_attr('" + D_AMIGO + "', 'longestSilenceMs') | float(0)) / 3600000) | round(0) | int }} h without being heard", "mdi:volume-off", "grey"),
    tpl("Clock", cs_relogio("amigo"), "mdi:clock-alert-outline",
        "{{ 'green' if state_attr('sensor.corescope_amigo_relogio', 'severity') == 'ok' else 'orange' }}", half=False),
    {"type": "markdown", "content": (
        "**Direct neighbors ({{ states('sensor.corescope_amigo_vizinhos') }})**\n\n| Repeater | Distance | SNR | Count | Last seen |\n|---|---|---|---|---|\n"
        "{% for n in (state_attr('sensor.corescope_amigo_vizinhos', 'neighbors') or []) | sort(attribute='count', reverse=true) %}"
        "| {{ n.name }} | {{ n.distance_km | default(0) | round(1) }} km | {{ n.avg_snr | round(1) }} | {{ n.count }} | {{ as_timestamp(n.last_seen) | timestamp_custom('%d/%m %H:%M') }} |\n{% endfor %}")},
]

CS_REG_SLUGS = [("reg_norte", "Norte"), ("reg_sul", "Sul"),
                ("reg_leste", "Leste"), ("reg_oeste", "Oeste")]
cs_tabela_jun = {"type": "markdown", "content": (
    "**Comparison (7 days)**\n\n| | Avail. | Signal | SNR | Pkts/day | Neighbors | Clock |\n|---|---|---|---|---|---|---|\n" + "".join(
        ("| {nome} | {{{{ states('sensor.corescope_S_disponibilidade') }}}}% | {{{{ state_attr('sensor.corescope_S_disponibilidade', 'signalGrade') }}}} "
         "| {{{{ state_attr('sensor.corescope_S_disponibilidade', 'snrMean') }}}} | {{{{ state_attr('sensor.corescope_S_disponibilidade', 'avgPacketsPerDay') | round(0) | int }}}} "
         "| {{{{ states('sensor.corescope_S_vizinhos') }}}} | REL |\n").format(nome=nome).replace("REL", cs_relogio(s)).replace("_S_", "_" + s + "_")
        for s, nome in CS_REG_SLUGS) +
    "\n**Most frequent neighbor**\n\n" + "".join(
        "- " + nome + ": {{ states('sensor.corescope_" + s + "_melhor_vizinho') }}\n" for s, nome in CS_REG_SLUGS))}

CS_AMIGO = "sensor.corescope_amigo"
CS_OBS = "sensor.corescope_amigo_observers"
cs_amigo = [
    heading("A friend's repeater (CoreScope)", "mdi:account-heart"),
    cs_no(CS_AMIGO, "REP-AMIGO-07C8"),
    tpl("Seen by the network (CoreScope)", "{% set a = [state_attr('sensor.corescope_amigo', 'last_heard'), state_attr('sensor.corescope_amigo', 'last_relayed')] | reject('none') | list %}{% set t = a | max if a else none %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) if t else 999 %}{% if t %}last heard {{ (h * 60) | int ~ ' min' if h < 1 else (h | int ~ ' h' if h < 48 else (h / 24) | int ~ ' days') }} ago{% else %}never heard{% endif %} · by {{ states('sensor.corescope_amigo_observers') }} observers · {{ (state_attr('sensor.corescope_amigo_observers', 'stats') or {}).packetsToday | default(0) }} pkts today", "mdi:ear-hearing", "{% set a = [state_attr('sensor.corescope_amigo', 'last_heard'), state_attr('sensor.corescope_amigo', 'last_relayed')] | reject('none') | list %}{% set t = a | max if a else none %}{% set h = ((now() - as_datetime(t)).total_seconds() / 3600) if t else 999 %}{{ 'green' if h < 1 else 'orange' if h < 24 else 'red' }}", half=False, entity="sensor.corescope_amigo",
        tap_action={"action": "url", "url_path": "https://corescope.example.org/"}),
    *cs_amigo_extra,
    tpl("Last advert", (cs_idade("last_heard") + " ago").replace("E", CS_AMIGO), "mdi:bullhorn", "blue"),
    tpl("Average hops", "{{ state_attr('" + CS_OBS + "', 'stats').avgHops | default('-') }} hops to the observers", "mdi:transit-connection-variant", "purple"),
    {"type": "markdown", "content": (
        "**Heard by ({{ states('" + CS_OBS + "') }} observers)**\n\n| Observer | RSSI | SNR | Packets |\n|---|---|---|---|\n"
        "{% for o in (state_attr('" + CS_OBS + "', 'observers') or []) | sort(attribute='packetCount', reverse=true) %}"
        "| {{ o.observer_name }} | {{ o.avgRssi | round(0) | int }} | {{ o.avgSnr | round(1) }} | {{ o.packetCount }} |\n{% endfor %}")},
    graf("Relays per 24h", "mdi:chart-line", [{"entity": CS_AMIGO, "name": "Friend", "color": "#eb5757"}], horas=168),
]

CS_JUN = [("sensor.corescope_reg_norte", "REP-NORTE-E28A"),
          ("sensor.corescope_reg_sul", "REP-SUL-786A"),
          ("sensor.corescope_reg_leste", "REP-LESTE-8A98"),
          ("sensor.corescope_reg_oeste", "REP-OESTE-E0BD")]
cs_regiao = [
    heading("Region (CoreScope)", "mdi:map-marker-radius"),
    *[cs_no(e, n) for e, n in CS_JUN],
    cs_tabela_jun,
    graf("Relays per 24h", "mdi:chart-line", [
        {"entity": e, "name": n.split("-")[1].title()} for e, n in CS_JUN], horas=168),
]

view_mesh = {
    "title": "Mesh", "path": "mesh", "icon": "mdi:access-point-network", "type": "sections", "max_columns": 3,
    "sections": [sec(*mesh_companion, *cs_amigo), sec(*mesh_repetidor, *cs_regiao), sec(*mesh_mensagens)],
}

# ---------- Rede (internet da operadora + Wi-Fi mesh Deco) ----------
NET_ON = "(is_state('binary_sensor.rede_cloudflare', 'on') or is_state('binary_sensor.rede_google', 'on'))"
rede_internet = [
    heading("Internet (operadora)", "mdi:web"),
    tpl("Internet",
        "{% if not is_state('binary_sensor.rede_modem', 'on') %}Modem não responde"
        "{% elif " + NET_ON + " %}Online · {{ states('sensor.rede_cloudflare_latencia') | float(0) | round(0) | int }} ms"
        " · perda {{ states('sensor.rede_cloudflare_perda') | float(0) | round(0) | int }}%"
        "{% else %}FORA DO AR (modem ok){% endif %}",
        "mdi:web",
        "{% if not is_state('binary_sensor.rede_modem', 'on') or not " + NET_ON + " %}red"
        "{% elif states('sensor.rede_cloudflare_perda') | float(0) > 5 or states('sensor.rede_cloudflare_latencia') | float(0) > 80 %}orange{% else %}green{% endif %}",
        half=False, entity="binary_sensor.rede_cloudflare", tap_action={"action": "more-info"}),
    tpl("IP público", "{{ states('sensor.internet_ip_publico') }} · desde {{ as_local(states.sensor.internet_ip_publico.last_changed).strftime('%d/%m %H:%M') }}",
        "mdi:ip-network", "blue", half=False, entity="sensor.internet_ip_publico", tap_action={"action": "more-info"}),
    tile("sensor.internet_download", "Download", "mdi:download", "green", 4),
    tile("sensor.internet_upload", "Upload", "mdi:upload", "purple", 4),
    tile("sensor.internet_ping", "Ping", "mdi:timer-outline", "teal", 4),
    tpl("Rodar speedtest agora", "Leva uns 30 segundos", "mdi:speedometer", "indigo", half=False,
        tap_action={"action": "perform-action", "perform_action": "homeassistant.update_entity",
                    "target": {"entity_id": "sensor.internet_download"}}),
    graf("Velocidade (7 dias)", "mdi:chart-line", [
        {"entity": "sensor.internet_download", "name": "Download", "color": "#27ae60"},
        {"entity": "sensor.internet_upload", "name": "Upload", "color": "#9b51e0"}], horas=168, pph=1),
]
def lat(slug, nome, icon):
    return tpl(nome,
               "{{ states('sensor.rede_S_latencia') | float(0) | round(1) }} ms · jitter {{ states('sensor.rede_S_jitter') | float(0) | round(1) }} · perda {{ states('sensor.rede_S_perda') | float(0) | round(0) | int }}%".replace("S_", slug + "_"),
               icon,
               "{% if not is_state('binary_sensor.rede_S', 'on') %}red{% elif states('sensor.rede_S_perda') | float(0) > 5 %}orange{% else %}green{% endif %}".replace("S'", slug + "'").replace("S_", slug + "_"),
               half=False, entity=f"sensor.rede_{slug}_latencia", tap_action={"action": "more-info"})
rede_latencia = [
    heading("Latência", "mdi:timer-sand"),
    lat("modem", "Modem da operadora (192.168.0.1)", "mdi:router-wireless"),
    lat("cloudflare", "Cloudflare (1.1.1.1)", "mdi:cloud-outline"),
    lat("google", "Google (8.8.8.8)", "mdi:google"),
    graf("Latência (24 h)", "mdi:chart-bell-curve", [
        {"entity": "sensor.rede_modem_latencia", "name": "Modem", "color": "#4f8bf7"},
        {"entity": "sensor.rede_cloudflare_latencia", "name": "Cloudflare", "color": "#f2994a"},
        {"entity": "sensor.rede_google_latencia", "name": "Google", "color": "#27ae60"}], horas=24, pph=4),
    {"type": "history-graph", "title": "Quedas (48 h)", "hours_to_show": 48,
     "entities": [{"entity": "binary_sensor.rede_modem", "name": "Modem"},
                  {"entity": "binary_sensor.rede_cloudflare", "name": "Cloudflare"},
                  {"entity": "binary_sensor.rede_google", "name": "Google"}]},
]

MBIT = " | float(0) * 8 / 1000) | round(1) }}"
def deco_card(slug, nome, extra):
    return tpl(f"Deco {nome}",
               "{% if is_state('binary_sensor.deco_S_online', 'on') %}{{ states('sensor.deco_S_connected_clients') }} aparelhos · X"
               "{% else %}OFFLINE{% endif %}".replace("S_", slug + "_").replace("X", extra),
               "mdi:router-wireless",
               "{{ 'green' if is_state('binary_sensor.deco_S_online', 'on') else 'red' }}".replace("S_", slug + "_"),
               half=False, entity=f"device_tracker.deco_{slug}", tap_action={"action": "more-info"})
def clientes(deco):
    return {"type": "markdown", "title": f"Conectados no Deco {deco}", "content": (
        "{% set banda = {'band2_4': '2,4 GHz', 'band5': '5 GHz', 'wired': 'Cabo'} %}"
        "{% set l = states.device_tracker | selectattr('entity_id', 'match', 'device_tracker.wifi_') | selectattr('state', 'eq', 'home')"
        " | selectattr('attributes.deco_device', 'eq', 'D') | sort(attribute='attributes.friendly_name') | list %}"
        "{% if l %}| Aparelho | Conexão | IP | ↓ kB/s | ↑ kB/s |\n|---|---|---|---:|---:|\n"
        "{% for s in l %}{% set a = s.attributes %}"
        "| {{ a.friendly_name | regex_replace('^(Sala|Office) Deco ', '') }} | {{ banda.get(a.connection_type, a.connection_type) }} | {{ a.ip or '-' }}"
        " | {{ a.down_kilobytes_per_s | default(0) | round(1) }} | {{ a.up_kilobytes_per_s | default(0) | round(1) }} |\n"
        "{% endfor %}\n{{ l | count }} aparelhos{% else %}Nenhum aparelho conectado{% endif %}").replace("'D'", f"'{deco}'")}
rede_deco = [
    heading("Wi-Fi mesh (Deco M4R)", "mdi:wifi"),
    deco_card("sala", "Sala (principal)",
              "CPU {{ states('sensor.deco_sala_cpu_usage') | int(0) }}% · memória {{ states('sensor.deco_sala_memory_usage') | int(0) }}%"),
    clientes("Sala"),
    deco_card("office", "Office",
              "ligado por {{ 'cabo' if is_state('sensor.deco_office_backhaul_type', 'wired') else 'Wi-Fi' }}"),
    clientes("Office"),
    tpl("Observer MeshCore no Wi-Fi",
        "{% if is_state('binary_sensor.rede_observer', 'on') %}Conectado (192.168.0.27) desde {{ as_local(states.binary_sensor.rede_observer.last_changed).strftime('%d/%m %H:%M') }}"
        "{% else %}Fora do Wi-Fi desde {{ as_local(states.binary_sensor.rede_observer.last_changed).strftime('%d/%m %H:%M') }}{% endif %}",
        "mdi:access-point-network",
        "{{ 'green' if is_state('binary_sensor.rede_observer', 'on') else 'red' }}",
        half=False, entity="binary_sensor.rede_observer", tap_action={"action": "more-info"}),
    tpl("Tráfego agora",
        "↓ {{ (states('sensor.deco_sala_total_down')" + MBIT + " · ↑ {{ (states('sensor.deco_sala_total_up')" + MBIT + " Mbit/s",
        "mdi:swap-vertical", "blue", half=False, entity="sensor.deco_sala_total_down", tap_action={"action": "more-info"}),
    graf("Tráfego Wi-Fi (24 h)", "mdi:chart-areaspline", [
        {"entity": "sensor.deco_sala_total_down", "name": "Download", "color": "#27ae60"},
        {"entity": "sensor.deco_sala_total_up", "name": "Upload", "color": "#9b51e0"}], horas=24, pph=4),
]
view_rede = {
    "title": "Rede", "path": "rede", "icon": "mdi:lan", "type": "sections", "max_columns": 3,
    "sections": [sec(*rede_internet), sec(*rede_latencia), sec(*rede_deco)],
}

config = {"title": "Casa", "views": [view_casa, view_sala, view_escritorio, view_externo, view_servidores, view_rede, view_mesh]}

cmds = []
if "--create" in sys.argv:
    cmds.append({"type": "lovelace/dashboards/create", "url_path": "painel-casa", "title": "Casa",
                 "icon": "mdi:home-variant", "show_in_sidebar": True, "require_admin": False, "mode": "storage"})
cmds.append({"type": "lovelace/config/save", "url_path": "painel-casa", "config": config})
print(json.dumps(cmds, ensure_ascii=False))
