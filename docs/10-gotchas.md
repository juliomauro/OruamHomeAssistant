# 10. Gotchas

Problems that showed up during the build, with the cause and the fix.

## Installation

### Reverse proxy ignored

- **Symptom:** after setting `http:` in YAML, Traefik still gets error 400, or the repair "ignored after migration" shows up.
- **Cause:** in 2026.11, `http:` migrates only once from YAML to `.storage/http`, and the `yaml_migration_done` flag prevents a new read.
- **Fix:**
  1. Configure it in the interface: **Settings > System > Network**, with X-Forwarded-For on and the trusted proxy `172.17.0.0/16`.
  2. If the interface does not offer the option, stop HA and set `yaml_migration_done` to `false` in `/config/.storage/http`. Edit it with a temporary container of the same image (`docker run --rm --entrypoint python3 -v /DATA/AppData/homeassistant/config:/config ...`) and start HA again.
  3. After the migration, **remove** the `http:` block from `configuration.yaml`.

### Backup fails

- **Symptom:** "Addons and folders are not supported by core backup".
- **Fix:** unselect folders and add-ons. A container install only backs up the configuration.

### Dashboard is not created

- **Symptom:** `lovelace/dashboards/create` rejects the `url_path`.
- **Fix:** the `url_path` must contain a hyphen. Example: `painel-casa`.

## API and scripts

| Symptom | Cause and fix |
|---|---|
| `auth_invalid` in `ha_ws.py` | The token file does not end with a newline. Use `{ cat ha_token; echo; ... }` |
| Config flow answers 400 | You sent a field the form does not ask for. Example: `count` on Ping. Send only the names listed in `data_schema` |
| DNS IP config flow answers 400 | Resolver and ports go inside the `additional_options` section |
| Rename fails with "entity already exists" | Two entities landed on the same ID (for example two `wlan0` devices). Rename one of them first |
| `NameError` in the dashboard generator | A card was used before it was defined. Move the definition up |
| `recorder/import_statistics` fails | `mean_type` and `unit_class` are missing from the metadata |

## Integrations

| Symptom | Cause and fix |
|---|---|
| Deco: "Unexpected error" | The host needs the `http://`. Example: `http://192.168.0.10` |
| Deco: "Invalid login credentials" | Use `admin` and the password of the owner account, not a manager account |
| Deco devices do not show up | The `device_tracker` entities come disabled. Run `deco_rename.py`, or enable them one by one |
| OctoPrint does not load | Webcam configured and not answering. Turn off the webcam in OctoPrint |
| Tuya plug energy goes back to zero | The Tuya counter is incremental. Use the integral (Riemann) over power |
| Smart Life key names do not arrive | Rename them in HA |
| Gemini: error 402 | The AI Studio account has no prepaid credit |
| YAML breaks with unit `%` | Add quotes: `unit_of_measurement: "%"` |
| `json_attributes_path` with a filter does not work | Use separate sensors with `selectattr` in the `value_template` |

## Templates

| Symptom | Cause and fix |
|---|---|
| Agenda out of order | Some calendars come in UTC. Sort by timestamp (`as_timestamp`), not by text |
| "desde 48 seconds" (English inside Portuguese text) | `relative_time` outputs English. Use `strftime('%H:%M')` or build the text yourself |
| "100.0%" | Use `\| float(0) \| int` |
| Latency sensor missing from the card | The Ping latency sensor only exists after the host answers for the first time. Do not use it in a card while the host is down |

## Dashboards

| Symptom | Cause and fix |
|---|---|
| card-mod font does not change on Mushroom 5 | The cards use `ha-tile-info`. Use `--ha-tile-info-primary-font-size` and the related variables, set on `ha-tile-info` itself |
| Large text gets cut | The `.vertical.fixed-info-height` class fixes the line height. Set `--ha-tile-info-primary-line-height` and `--ha-tile-info-primary-min-height` on `ha-tile-info` |
| Cards stuck together, no border | The `panel` view resets border and rounded corners. Apply `border-radius` and `border` with `!important` to each card through card-mod |
| Only 2 columns fit on the tablet | The `sections` view needs at least 320 px per column. On a ~1000 point screen, use `panel` + `horizontal-stack` |
| card-mod ignored on `horizontal-stack` | The stack does not load card-mod. Use `stack-card-gap` in the theme for spacing, and style each card |

## Telegram

| Symptom | Cause and fix |
|---|---|
| `httpx.ConnectError` once in a while | No IPv6 egress in the container. Use `continue_on_error: true`, and the next attempt works |
| Bot does not answer | The chat is not in `allowed_chat_ids`, or the `user_id` does not match the automation condition |
| Button keeps "loading" | `telegram_bot.answer_callback_query` is missing |
| Command not recognized in a group | Telegram sends `/status@bot_name`. Remove the suffix with `regex_replace('@.*', '')` |

## Security

- Do not turn on UPnP on the modem just to get metrics.
- Cheap IoT cameras often have telnet open. If there is no supported alternative firmware, keep the camera without internet access or replace it. An isolated guest network would cut the RTSP feed to HA.
- Do not expose HA directly to the internet. Use Tailscale or another VPN.
