# agenda_template.py v1.2 - insere (ou substitui) o sensor "Agenda hoje" (calendar.get_events) no bloco template: do configuration.yaml
# uso (no atlas): python3 agenda_template.py <arquivo_entrada> > <arquivo_saida>
import sys
BLOCO = '''  # Agenda: eventos de hoje e amanha para o painel do tablet
  - trigger:
      - trigger: time_pattern
        minutes: "/10"
      - trigger: homeassistant
        event: start
      - trigger: event
        event_type: agenda_atualizar
    action:
      - action: calendar.get_events
        target:
          entity_id:
            - calendar.pessoal
            - calendar.familia
            - calendar.birthdays
            - calendar.feriados_no_brasil
            - calendar.f1
            - calendar.escola
        data:
          start_date_time: "{{ today_at() }}"
          end_date_time: "{{ today_at() + timedelta(days=2) }}"
        response_variable: agenda
    sensor:
      - name: Agenda hoje
        unique_id: agenda_hoje
        icon: mdi:calendar-today
        state: >-
          {% set ini = as_timestamp(today_at()) %}{% set fim = ini + 86400 %}
          {% set ns = namespace(n=0) %}
          {% for cal, v in agenda.items() %}{% for e in v.events %}
          {% if as_timestamp(e.start, 0) < fim and as_timestamp(e.end, 0) > ini %}{% set ns.n = ns.n + 1 %}{% endif %}
          {% endfor %}{% endfor %}
          {{ ns.n }}
        attributes:
          eventos: >-
            {% set ns = namespace(l=[]) %}
            {% for cal, v in agenda.items() %}{% for e in v.events %}
            {% set ns.l = ns.l + [{'ts': as_timestamp(e.start, 0) | int, 'te': as_timestamp(e.end, 0) | int, 'dia_todo': e.start | length == 10,
               'titulo': e.summary, 'agenda': state_attr(cal, 'friendly_name')}] %}
            {% endfor %}{% endfor %}
            {{ ns.l | sort(attribute='ts') }}
'''
txt = open(sys.argv[1]).read()
MARCA = "  # Agenda: eventos de hoje e amanha para o painel do tablet\n"
if MARCA in txt:  # substitui o bloco antigo (vai ate o proximo item "  - trigger:" que nao seja o dele)
    a = txt.index(MARCA)
    b = txt.index("\n  - trigger:", txt.index("unique_id: agenda_hoje", a)) + 1
    txt = txt[:a] + txt[b:]
assert txt.count("\ntemplate:\n") == 1
sys.stdout.write(txt.replace("\ntemplate:\n", "\ntemplate:\n" + BLOCO, 1))
