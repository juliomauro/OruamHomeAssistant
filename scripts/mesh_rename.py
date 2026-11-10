# mesh_rename.py v1.0 - renomeia entidades MeshCore para ids curtos
import json
C = "sensor.meshcore_c0ffee_%s_casa_companion"
R = "sensor.meshcore_438702360c_%s_rep_casa_4387"
comp = {"node_status":"status","battery_voltage":"bateria_v","battery_percentage":"bateria","frequency":"frequencia",
        "bandwidth":"banda","spreading_factor":"sf","tx_power":"potencia","uptime":"uptime","noise_floor":"ruido",
        "last_rssi":"rssi","last_snr":"snr","nb_recv":"recebidas","nb_sent":"enviadas","recv_errors":"erros",
        "tx_airtime":"tx_airtime","rx_airtime":"rx_airtime","last_message_delivery":"ultima_entrega",
        "temperature_ch1":"temperatura"}
rep = {"bat":"bateria_v","battery_percentage":"bateria","uptime":"uptime","noise_floor":"ruido","last_rssi":"rssi",
       "last_snr":"snr","nb_sent":"enviadas","nb_recv":"recebidas","recv_errors":"erros","flood_dups":"dup_flood",
       "airtime":"airtime","airtime_utilization":"uso_airtime","ch1_temperature":"temperatura",
       "full_evts":"fila_cheia","request_failures":"falhas","request_successes":"sucessos"}
m = {C % k: "sensor.mesh_" + v for k, v in comp.items()}
m.update({R % k: "sensor.repetidor_" + v for k, v in rep.items()})
m.update({"update.meshcore_c0ffee_firmware": "update.mesh_firmware",
          "update.meshcore_438702360c_firmware": "update.repetidor_firmware",
          "sensor.meshcore_438702360c_neighbor_count": "sensor.repetidor_vizinhos",
          "binary_sensor.meshcore_438702360c_online_rep_casa_4387": "binary_sensor.repetidor_online"})
print(json.dumps([{"type": "config/entity_registry/update", "entity_id": a, "new_entity_id": b} for a, b in m.items()]))
