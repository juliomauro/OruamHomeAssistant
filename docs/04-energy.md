# 4. Energy (office Tuya plug)

The goal is to see the consumption of the office desk setup per day and per month, in kWh and in money, with history since 2023.

## 4.1 Why not use the plug's energy sensor

The Tuya plug reports energy **incrementally**: the counter goes back to zero when the integration reloads. So consumption is computed from **power** (W), with the **Integral (Riemann sum)** helper:

| Field | Value |
|---|---|
| Name | Setup escritório energia |
| Source | `sensor.escritorio_mesa_potencia` |
| Method | left |
| Metric prefix | k |
| Time unit | h |
| Max sub-interval | 5 min |

The result is the sensor `sensor.setup_escritorio_energia`, in kWh.

## 4.2 Meters and cost

`energia.py` creates, through config flows:

- the utility meters `sensor.setup_escritorio_hoje` (daily) and `sensor.setup_escritorio_mes` (monthly);
- the templates `sensor.custo_setup_hoje` and `sensor.custo_setup_mes` (cost today, cost this month), in BRL.

```bash
python3 energia.py   # reads ./ha_token
```

The price per kWh lives in a **Number** helper, `input_number.preco_do_kwh`. In my case it is R$ 1.0133: the distributor's B1 residential rate of 0.7397, plus about 27% of taxes.

The cost is computed like this:

```jinja
{{ (states('sensor.setup_escritorio_mes') | float(0) * states('input_number.preco_do_kwh') | float(0)) | round(2) }}
```

## 4.3 Import the app history

The Smart Life app shows consumption month by month. `historico_tomada.py` turns those numbers into an external statistic, `tuya:setup_escritorio_historico`, which the `statistics-graph` card shows as monthly bars.

```bash
python3 historico_tomada.py > cmd.json
{ cat ../ha_token; echo; cat cmd.json; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

`recorder/import_statistics` requires `mean_type` and `unit_class` in the metadata. Without them, the import fails.
