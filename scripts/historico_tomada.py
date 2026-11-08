# historico_tomada.py v1.0 - gera o comando de importacao do historico mensal (app Smart Life) da tomada do escritorio
# Uso: python3 historico_tomada.py > cmd.json
import json, calendar
from datetime import datetime, timedelta, timezone

TZ = timezone(timedelta(hours=-3))  # America/Sao_Paulo (sem horario de verao)

# kWh por mes, do app Smart Life (prints de 2026-11-07)
DADOS = {
    2023: {11: 24.34, 12: 20.91},
    2024: {1: 17.24, 2: 12.12, 3: 13.05, 4: 14.96, 5: 12.35, 6: 12.06, 7: 16.40, 8: 23.96, 9: 23.17, 10: 24.12, 11: 34.97, 12: 47.51},
    2025: {1: 52.18, 2: 53.25, 3: 61.11, 4: 52.26, 5: 47.77, 6: 37.47, 7: 51.09, 8: 56.77, 9: 47.39, 10: 54.39, 11: 33.00, 12: 39.44},
    2026: {1: 29.83, 2: 27.34, 3: 41.73, 4: 24.32, 5: 51.54, 6: 53.19, 7: 44.63, 8: 56.80, 9: 53.52, 10: 61.47},
}
# Novembro/2026 so ate o dia 6 (15.09 do mes - 1.55 de hoje); do dia 7 em diante o HA mede
PARCIAL = (2026, 11, 6, round(15.09 - 1.55, 2))

stats, soma = [], 0.0
for ano in sorted(DADOS):
    for mes in sorted(DADOS[ano]):
        soma = round(soma + DADOS[ano][mes], 2)
        ultimo = calendar.monthrange(ano, mes)[1]
        stats.append({"start": datetime(ano, mes, ultimo, 23, tzinfo=TZ).isoformat(), "state": soma, "sum": soma})
a, m, d, v = PARCIAL
soma = round(soma + v, 2)
stats.append({"start": datetime(a, m, d, 23, tzinfo=TZ).isoformat(), "state": soma, "sum": soma})

cmd = [{"type": "recorder/import_statistics",
        "metadata": {"has_sum": True, "mean_type": 0, "name": "Setup escritório (histórico Smart Life)",
                     "source": "tuya", "statistic_id": "tuya:setup_escritorio_historico",
                     "unit_class": "energy", "unit_of_measurement": "kWh"},
        "stats": stats}]
print(json.dumps(cmd, ensure_ascii=False))
