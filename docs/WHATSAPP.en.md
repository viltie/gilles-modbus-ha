# Gilles alerts to WhatsApp

> [🇫🇮 Suomi](WHATSAPP.md) · 🇬🇧 **English**

`packages/gilles_whatsapp.yaml` sends boiler alerts to a WhatsApp group and answers **`!tila`** ("status") in the group. Messages go through a [WAHA](https://waha.devlike.pro) bridge (WhatsApp HTTP API). The package only reads boiler data; it never writes to the boiler. Message texts are in Finnish.

## Alerts

| Alert | When |
|---|---|
| 🔴 Connection to boiler lost | no complete Modbus data for 10 min; another message when it returns |
| 🟠 Ignition phase too long | `binary_sensor.gilles_startphase_zu_lang` (threshold adjustable on the dashboard) |
| 🟠 Temperature not rising after start | `binary_sensor.gilles_temperaturanstieg_fehlt` for over 25 min (it briefly turns on in normal running, hence the long delay) |
| 🟠 Frequent starts | starts in 24 h above the threshold, at most once per 12 h |
| 🟠 / 🔴 Start aborted / boiler went out | status code 31 (start aborted) or 34 (probably "no fire") – not in the upstream project |
| 🔴 Boiler cooling | boiler below 50 °C for 15 min |

**`!tila`** in the group replies with a snapshot: burner phase, boiler and system state, boiler/flue gas/return temperatures, residual oxygen, fuel store temperature and starts in 24 h.

If a WhatsApp send fails (WAHA session dropped), the same message goes to your phone as a Home Assistant notification.

## Setup

1. **WAHA** – run it in Docker on the same LAN as Home Assistant (see the Finnish guide for an example `docker run`), start session `default` in the WAHA dashboard and link it to WhatsApp with the QR code (*WhatsApp → Linked devices*). A separate number for alerts is recommended. Do not expose WAHA to the internet.
2. **Group id** – create a group, add the linked number, and read its `chatId` (`120363…@g.us`) from WAHA's Swagger: `GET /api/default/groups`.
3. **Webhook for `!tila`** – set the session webhook to `http://HA-ADDRESS:8123/api/webhook/<gilles_whatsapp_webhook>` with event `message.any` (WAHA dashboard session settings, or `PUT /api/sessions/default` → `config.webhooks`). The HA webhook is `local_only`. WAHA forwards every message of the account; the package only reacts to `!tila` in your group and keeps no automation traces.
4. **Home Assistant** – copy `packages/gilles_whatsapp.yaml` to `packages/` (the other Gilles packages and the setup script's helpers must be installed), add the secrets as in `secrets.example.yaml`, replace `notify.mobile_app_puhelin` with your phone's notify service, check the config and restart.

Test by sending `!tila` in the group.
