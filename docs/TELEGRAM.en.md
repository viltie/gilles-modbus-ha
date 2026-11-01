# Gilles alerts to Telegram

> [🇫🇮 Suomi](TELEGRAM.md) · 🇬🇧 **English**

`packages/gilles_telegram.yaml` sends boiler alerts to a Telegram group or private chat and answers **`/tila`** ("status", or `!tila`). Messages go through Home Assistant's own [Telegram bot integration](https://www.home-assistant.io/integrations/telegram_bot/). The package only reads boiler data; it never writes to the boiler. Message texts are in Finnish.

**Telegram is the recommended channel.** It is free, uses Telegram's official bot API, needs no extra phone number or SIM card, and Home Assistant does not have to be reachable from the internet. WhatsApp alerts ([WHATSAPP.en.md](WHATSAPP.en.md)) go through the unofficial WAHA bridge, which needs its own WhatsApp number and can lose its session. Both channels can also run side by side.

## Alerts

The alert automations live in `gilles_halytykset.yaml` and send to every installed channel.

| Alert | When |
|---|---|
| 🔴 Connection to boiler lost | no complete Modbus data for 10 min; another message when it returns |
| 🟠 Ignition phase too long | `binary_sensor.gilles_startphase_zu_lang` (threshold adjustable on the dashboard) |
| 🟠 Temperature not rising after start | `binary_sensor.gilles_temperaturanstieg_fehlt` for over 25 min (it briefly turns on in normal running, hence the long delay) |
| 🟠 Frequent starts | starts in 24 h above the threshold, at most once per 12 h |
| 🟠 / 🔴 Start aborted / boiler went out | status code 31 (start aborted) or 34 (probably "no fire") – not in the upstream project |
| 🔴 Boiler cooling | boiler below 50 °C for 15 min |

**`/tila`** replies with a snapshot: burner phase, boiler and system state, boiler/flue gas/return temperatures, residual oxygen, fuel store temperature and starts in 24 h. The package only answers in the chat(s) set in `secrets.yaml`, at most once per 30 seconds.

If a Telegram send fails, the same message goes to your phone as a Home Assistant notification.

## Setup

Requires Home Assistant 2026.6 or newer.

1. **Bot** – in Telegram, open [@BotFather](https://t.me/BotFather), send `/newbot`, choose a name and a username ending in `bot`. Keep the **API token** (`123456789:AA…`) secret.
2. **Integration** – *Settings → Devices & services → Add integration → Telegram bot*. Choose **Platform: Polling** (fetches messages itself, so HA need not be exposed to the internet; *Broadcast* cannot receive `/tila`, *Webhooks* needs a public HTTPS URL) and paste the token as **API key**.
3. **Chat ID** – private chat: open your bot and send `/start` (bots cannot start a conversation). Group: create a group, add the people and the bot, and send `/start` in it. A private chat ID is positive, a group's is negative (`-100…` for supergroups). The easiest way to read it is the HA log (*Settings → System → Logs*): a message from a chat that is not yet allowed logs *"Unauthorized update - neither user id … nor chat id … is in allowed chats"*; the `chat id` is the one you need. For a private chat, [@id_bot](https://t.me/id_bot) also tells you your ID.
4. **Allow the chat** – *Settings → Devices & services → Telegram bot*, three-dot menu of the bot entry → **Add allowed chat ID**.
5. **Packages and secrets** – copy `packages/gilles_halytykset.yaml` and `packages/gilles_telegram.yaml` to `packages/` (the other Gilles packages and the setup script's helpers must be installed). Add `gilles_telegram_chat_id: -1001234567890` to `secrets.yaml` (or a list such as `[-1001234567890, 123456789]`; every ID must be allowed in step 4). Replace `notify.mobile_app_puhelin` in `gilles_halytykset.yaml` with your phone's notify service, check the config and restart.

Test by sending `/tila` in the chat, or run `script.gilles_halytys` with `message: testi` from *Developer tools → Actions*.

## Groups and privacy mode

Bots have **privacy mode** on by default. In a group the bot then only sees commands addressed to it (`/tila@YourBot`), general commands (`/tila`) if it was the last bot to post in the group, and replies to its own messages. With no other bots in the group `/tila` therefore always works, but `!tila` needs privacy mode off:

- BotFather → `/setprivacy` → choose the bot → **Disable**, then remove the bot from the group and add it again (the change only applies after re-adding).
- Alternatively, make the bot a group admin.

Without privacy mode the bot receives every group message. The package only reacts to the status command and keeps no automation traces.

To show the command in the bot's menu: BotFather → `/setcommands` → `tila - Kattilan tila nyt`.

If a basic group is upgraded to a supergroup (e.g. when admins are added), its chat ID changes. Allow the new ID and update `secrets.yaml`.

## Several bots

If HA has more than one Telegram bot, add `config_entry_id:` (the bot's config entry ID) to the send in script `gilles_telegram_viesti`, otherwise HA cannot tell which bot to use. The `/tila` reply automatically uses the bot that received the command.
