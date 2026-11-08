# 4. Energia (tomada Tuya do escritório)

O objetivo é ver o consumo do setup do escritório no dia e no mês, em kWh e em R$, com o histórico desde 2023.

## 4.1 Por que não usar o sensor de energia da tomada

A tomada Tuya informa a energia de forma **incremental**: o contador volta a zero quando a integração recarrega. Por isso o consumo é calculado a partir da **potência** (W), com o helper **Integral (soma de Riemann)**:

| Campo | Valor |
|---|---|
| Nome | Setup escritório energia |
| Fonte | `sensor.escritorio_mesa_potencia` |
| Método | left |
| Prefixo | k |
| Tempo | h |
| Intervalo máximo | 5 min |

O resultado é o sensor `sensor.setup_escritorio_energia`, em kWh.

## 4.2 Medidores e custo

O `energia.py` cria, por config flow:

- os utility meters `sensor.setup_escritorio_hoje` (diário) e `sensor.setup_escritorio_mes` (mensal);
- os templates `sensor.custo_setup_hoje` e `sensor.custo_setup_mes`, em BRL.

```bash
python3 energia.py   # lê ./ha_token
```

O preço do kWh fica em um helper **Número**, `input_number.preco_do_kwh`. No meu caso é R$ 1,0133: tarifa B1 da distribuidora, de 0,7397, mais cerca de 27% de impostos.

O custo é calculado assim:

```jinja
{{ (states('sensor.setup_escritorio_mes') | float(0) * states('input_number.preco_do_kwh') | float(0)) | round(2) }}
```

## 4.3 Importar o histórico do app

O app Smart Life mostra o consumo mês a mês. O `historico_tomada.py` transforma esses números em uma estatística externa, `tuya:setup_escritorio_historico`, que o card `statistics-graph` mostra em barras por mês.

```bash
python3 historico_tomada.py > cmd.json
{ cat ../ha_token; echo; cat cmd.json; } | docker exec -i homeassistant python3 -c "$(cat ha_ws.py)"
```

O `recorder/import_statistics` exige `mean_type` e `unit_class` no metadata. Sem esses campos, a importação falha.
