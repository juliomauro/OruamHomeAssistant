# 9. Telegram bot

The bot sends house alerts (new Wi-Fi device, door, internet, servers, rain, good morning) and answers commands (`/status`, `/rede`, `/agenda`, `/speedtest`, `/apagar`). Some alerts have buttons. The bot texts are in Portuguese.

## 9.1 Create the bot

1. In Telegram, talk to **@BotFather** and send `/newbot`.
2. Choose the bot name and username (it must end in `bot`).
3. BotFather returns the **bot token**. It gives full control of the bot: do not paste it in a chat, script or repository. It will only be typed in the HA interface, in step 9.2.

## 9.2 HA integration

1. **Settings > Devices & services > Add integration > Telegram bot**.
2. Platform: **Polling**. No open port or public webhook needed.
3. Paste the bot token.
4. Send `/start` to the bot.
5. Find your **chat ID**: in **Developer tools > Events**, listen to `telegram_command` and send `/start` again. The event carries `chat_id` and `user_id`.
6. In the integration, under **Add allowed chat** (`allowed_chat_ids`), register that chat ID. The bot ignores messages from chats that are not on this list.
7. Write down the integration **entry_id**. It shows in the URL of the integration page and in `GET /api/config/config_entries/entry`.

To send buttons, use `telegram_bot.send_message` with `config_entry_id` and `chat_id`. The `notify.<name>` service does not accept a keyboard.

Do not use the old `target` parameter: it is deprecated and stops working in HA 2026.9. HA shows a repair "The `target` parameter for Telegram Bot is being removed" for each automation that still uses it.

```yaml
action: telegram_bot.send_message
data:
  config_entry_id: YOUR_CONFIG_ENTRY_ID
  chat_id: 123456789
  parse_mode: html
  message: "<b>Bot</b> test"
  inline_keyboard:
    - "✅ Yes:/answer_yes, ❌ No:/answer_no"
```

## 9.3 Install the automations

`telegram_automacoes.py` creates or replaces all the automations through the API. Personal values come from environment variables:

```bash
docker exec homeassistant cp /config/automations.yaml /config/automations.yaml.bak-telegram
TG_ENTRY=YOUR_CONFIG_ENTRY_ID TG_CHAT=123456789 HA_URL=http://192.168.0.240:8123 \
  python3 telegram_automacoes.py "$(cat ../ha_token)"
```

Before running it:

- install the template sensors from [guide 7](07-template-sensors.md) (agenda, rain, night log);
- adjust the entity lists at the top of the script (`LUZES` lights, the `OP` printer, the server sensors).

The script also adds the Telegram message at the start of two existing automations: `porta_aberta_madrugada` and `observer_wifi`.

## 9.4 Alerts

| Automation | When it alerts |
|---|---|
| `wifi_aparelho_novo` | A never seen MAC joined a Deco. Comes with the buttons **✅ Conheço** (I know it) and **🚫 Como bloquear?** (how to block?) |
| `porta_aberta_madrugada` | Front door opened between 23:30 and 06:00. Also speaks on the speaker |
| `telegram_internet` | Internet came back after more than 2 min down, with the time and length of the outage. During the outage the message would not get through |
| `telegram_deco_offline` | A Deco was offline for 3 min, and when it comes back |
| `observer_wifi` | The MeshCore observer has not answered ping for 2 h, or is back after that |
| `telegram_impressora` | The 3D print finished (says if it ended with an error) |
| `telegram_chuva` | `binary_sensor.chuva_chegando` turned on, only from 07:00 to 22:30 and at most once every 3 h |
| `telegram_servidores` | Disk above 90%, temperature above 80 °C for 10 min, boreas not answering for 5 min (and when it is back), Traefik down for 3 min (and when it is back), Pi-hole not blocking for 30 min, certificate expiring in less than 20 days (checked at 10:00), atlas rebooted |
| `telegram_bom_dia` | Every day at 07:30 |

### Good morning

The message has:

- the day's weather (condition in Portuguese, low and high);
- the expected rain window, from the hourly forecast;
- today's agenda;
- what happened during the night (`sensor.diario_da_noite`), or "tranquila" (quiet);
- internet speed;
- server problems, or "tudo ok" (all good).

To test without waiting for 07:30, fire the `bom_dia_teste` event in **Developer tools > Events**.

### Buttons (callbacks)

When a button is tapped, HA receives the `telegram_callback` event, which carries `data` (for example `/wifi_conheco tv`), `id`, `chat_id` and `message.message_id`. The automation then:

1. answers with `telegram_bot.answer_callback_query`, which removes the "loading" state of the button;
2. edits the original message with `telegram_bot.edit_message`, to remove the buttons and show the result.

Every command or button automation checks `trigger.event.data.user_id` against your ID, on top of the `allowed_chat_ids` list.

Blocking a device from the bot is on hold: the Deco integration has no block service. The "Como bloquear?" button only explains the path in the Deco app.

## 9.5 Commands

| Command | Answer |
|---|---|
| `/status` | Door, internet (latency and download), lights on, kitchen temperature, Rubi, printer, devices per Deco, next calendar event |
| `/rede` (network) | Who is on each Deco, with the band (2.4, 5G or cable) |
| `/agenda` | Today and tomorrow. Before answering, it forces an update of `sensor.agenda_hoje` |
| `/speedtest` | Runs a speedtest right away (about 30 s) and answers download, upload and ping |
| `/apagar` (turn off) | Lists the lights that are on and asks for confirmation with buttons |
| anything else (`/ajuda`, `/start`) | Command list |

The `telegram_comandos` automation listens to the `telegram_command` event. The command name is compared after removing the `@bot_name` suffix that Telegram adds in groups: `trigger.event.data.command | regex_replace('@.*', '')`.

### Command menu in Telegram

To make the commands show up when you type `/`, send `/setcommands` to @BotFather, pick the bot and paste:

```
status - resumo da casa
rede - quem está no Wi-Fi
agenda - hoje e amanhã
speedtest - mede a internet agora
apagar - apaga todas as luzes
ajuda - lista os comandos
```

## 9.6 Known issues

- **`httpx.ConnectError` on the first send:** the container has no IPv6 egress, and the first attempt sometimes goes over IPv6. The send actions use `continue_on_error: true`, so one of these errors does not stop the rest of the automation.
- **To see why a message did not arrive:** open the automation trace, in **Settings > Automations > ⋮ > Traces**.
