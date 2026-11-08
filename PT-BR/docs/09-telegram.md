# 9. Bot do Telegram

O bot manda alertas da casa (aparelho novo no Wi-Fi, porta, internet, servidores, chuva, bom dia) e responde a comandos (`/status`, `/rede`, `/agenda`, `/speedtest`, `/apagar`). Alguns alertas têm botões.

## 9.1 Criar o bot

1. No Telegram, fale com o **@BotFather** e mande `/newbot`.
2. Escolha o nome e o usuário do bot (precisa terminar em `bot`).
3. O BotFather devolve o **token do bot**. Ele dá controle total do bot: não cole em chat, script nem repositório. Ele só vai ser digitado na interface do HA, no passo 9.2.

## 9.2 Integração no HA

1. **Configurações > Dispositivos e serviços > Adicionar integração > Telegram bot**.
2. Plataforma: **Polling**. Não precisa de porta aberta nem de webhook público.
3. Cole o token do bot.
4. No bot, mande `/start` para ele.
5. Descubra seu **chat ID**: em **Ferramentas de desenvolvedor > Eventos**, escute `telegram_command` e mande `/start` de novo. O evento traz `chat_id` e `user_id`.
6. Na integração, em **Adicionar chat permitido** (`allowed_chat_ids`), cadastre esse chat ID. O bot ignora mensagens de chats que não estão nessa lista.
7. Anote o **entry_id** da integração. Ele aparece na URL da página da integração e em `GET /api/config/config_entries/entry`.

Para enviar com botões, use `telegram_bot.send_message` com `config_entry_id` e `chat_id`. O serviço `notify.<nome>` não aceita teclado.

Não use o parâmetro antigo `target`: ele está obsoleto e para de funcionar no HA 2026.9. O HA mostra um reparo "The `target` parameter for Telegram Bot is being removed" para cada automação que ainda usa.

```yaml
action: telegram_bot.send_message
data:
  config_entry_id: SEU_CONFIG_ENTRY_ID
  chat_id: 123456789
  parse_mode: html
  message: "<b>Teste</b> do bot"
  inline_keyboard:
    - "✅ Sim:/resposta_sim, ❌ Não:/resposta_nao"
```

## 9.3 Instalar as automações

O `telegram_automacoes.py` cria ou substitui todas as automações pela API. Os valores pessoais vêm por variável de ambiente:

```bash
docker exec homeassistant cp /config/automations.yaml /config/automations.yaml.bak-telegram
TG_ENTRY=SEU_CONFIG_ENTRY_ID TG_CHAT=123456789 HA_URL=http://192.168.0.240:8123 \
  python3 telegram_automacoes.py "$(cat ../ha_token)"
```

Antes de rodar:

- instale os sensores de template do [guia 7](07-sensores-template.md) (agenda, chuva, diário da noite);
- ajuste as listas de entidades no topo do script (`LUZES`, a impressora `OP`, os sensores de servidor).

O script também acrescenta o envio para o Telegram no início de duas automações que já existem: `porta_aberta_madrugada` e `observer_wifi`.

## 9.4 Alertas

| Automação | Quando avisa |
|---|---|
| `wifi_aparelho_novo` | MAC nunca visto conectou em um Deco. Vem com os botões **✅ Conheço** e **🚫 Como bloquear?** |
| `porta_aberta_madrugada` | Porta de entrada abriu entre 23:30 e 06:00. Também fala no alto-falante |
| `telegram_internet` | A internet voltou depois de mais de 2 min fora, com o horário e a duração da queda. Durante a queda a mensagem não chegaria |
| `telegram_deco_offline` | Um Deco ficou offline por 3 min, e quando ele volta |
| `observer_wifi` | O observer MeshCore entrou no Wi-Fi ou saiu por 10 min |
| `telegram_impressora` | A impressão 3D terminou (avisa se foi com erro) |
| `telegram_chuva` | `binary_sensor.chuva_chegando` ligou, só das 07:00 às 22:30 e no máximo 1 vez a cada 3 h |
| `telegram_servidores` | Disco acima de 90%, temperatura acima de 80 °C por 10 min, boreas sem resposta por 5 min (e a volta), Traefik fora por 3 min (e a volta), Pi-hole sem bloquear por 30 min, certificado vencendo em menos de 20 dias (checado às 10:00), atlas reiniciou |
| `telegram_bom_dia` | Todo dia às 07:30 |

### Bom dia

A mensagem traz:

- tempo do dia (condição em português, mínima e máxima);
- janela de chuva prevista, pela previsão horária;
- agenda de hoje;
- o que aconteceu de noite (`sensor.diario_da_noite`), ou "tranquila";
- velocidade da internet;
- problemas nos servidores, ou "tudo ok".

Para testar sem esperar até 07:30, dispare o evento `bom_dia_teste` em **Ferramentas de desenvolvedor > Eventos**.

### Botões (callbacks)

Ao tocar um botão, o HA recebe o evento `telegram_callback`, que traz `data` (Ex: `/wifi_conheco tv`), `id`, `chat_id` e `message.message_id`. A automação então:

1. responde com `telegram_bot.answer_callback_query`, que tira o "carregando" do botão;
2. edita a mensagem original com `telegram_bot.edit_message`, para tirar os botões e mostrar o resultado.

Toda automação de comando ou botão confere `trigger.event.data.user_id` contra o seu ID, além da lista `allowed_chat_ids`.

O bloqueio de aparelho pelo bot ficou em suspenso: a integração do Deco não tem serviço de bloqueio. O botão "Como bloquear?" só explica o caminho no app Deco.

## 9.5 Comandos

| Comando | Resposta |
|---|---|
| `/status` | Porta, internet (latência e download), luzes acesas, temperatura da cozinha, Rubi, impressora, aparelhos por Deco, próximo evento da agenda |
| `/rede` | Quem está em cada Deco, com a banda (2,4, 5G ou cabo) |
| `/agenda` | Hoje e amanhã. Antes de responder, força a atualização do `sensor.agenda_hoje` |
| `/speedtest` | Roda o speedtest na hora (cerca de 30 s) e responde download, upload e ping |
| `/apagar` | Lista as luzes acesas e pede confirmação com botões |
| qualquer outro (`/ajuda`, `/start`) | Lista de comandos |

A automação `telegram_comandos` escuta o evento `telegram_command`. O nome do comando é comparado depois de tirar o `@nome_do_bot`, que o Telegram acrescenta em grupos: `trigger.event.data.command | regex_replace('@.*', '')`.

### Menu de comandos no Telegram

Para os comandos aparecerem quando você digita `/`, mande `/setcommands` para o @BotFather, escolha o bot e cole:

```
status - resumo da casa
rede - quem está no Wi-Fi
agenda - hoje e amanhã
speedtest - mede a internet agora
apagar - apaga todas as luzes
ajuda - lista os comandos
```

## 9.6 Problemas conhecidos

- **`httpx.ConnectError` no primeiro envio:** o container não tem saída IPv6, e a primeira tentativa às vezes vai por IPv6. As ações de envio usam `continue_on_error: true`, para um erro desses não parar o resto da automação.
- **Para ver por que uma mensagem não chegou:** abra o trace da automação, em **Configurações > Automações > ⋮ > Traces**.
