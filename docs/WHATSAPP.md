# Gilles-hälytykset WhatsAppiin

> 🇫🇮 **Suomi** · [🇬🇧 English](WHATSAPP.en.md)

`packages/gilles_whatsapp.yaml` lähettää kattilan hälytykset WhatsApp-ryhmään ja vastaa ryhmässä komentoon **`!tila`**. Viestit kulkevat [WAHA](https://waha.devlike.pro)-sillan (WhatsApp HTTP API) kautta. Paketti vain lukee kattilan tietoja, se ei kirjoita kattilalle mitään.

## Hälytykset

| Hälytys | Milloin |
|---|---|
| 🔴 Yhteys kattilaan poikki | Modbus-data puuttuu yli 10 min; ilmoitus myös, kun yhteys palaa |
| 🟠 Sytytysvaihe liian pitkä | `binary_sensor.gilles_startphase_zu_lang` (raja säädettävissä kojelaudalta) |
| 🟠 Lämpötila ei nouse käynnistyksen jälkeen | `binary_sensor.gilles_temperaturanstieg_fehlt` yli 25 min (normaalikäytössä tämä menee päälle lyhyesti, siksi pitkä viive) |
| 🟠 Tiheät käynnistykset | käynnistyksiä 24 h yli rajan, korkeintaan kerran 12 h:ssa |
| 🟠 / 🔴 Käynnistys keskeytyi / kattila sammui | tilakoodi 31 (käynnistys keskeytyi) tai 34 (todennäköisesti "Ei tulta") – näitä ei ole alkuperäisessä projektissa |
| 🔴 Kattila jäähtyy | kattilan lämpötila alle 50 °C yli 15 min |

**`!tila`** ryhmässä vastaa hetken tilanteella: polttovaihe, kattilan ja laitteiston tila, kattila-, savukaasu- ja paluuveden lämpötila, jäännöshappi, polttoainevaraston lämpötila ja käynnistykset 24 h.

Jos WhatsApp-lähetys epäonnistuu (WAHA-istunto katkeaa), sama viesti lähetetään puhelimen HA-ilmoituksena.

## Asennus

### 1. WAHA

Aja WAHA Dockerissa samassa lähiverkossa kuin Home Assistant, esimerkiksi:

```bash
docker run -d --name waha --restart unless-stopped -p 3000:3000 \
  -e WHATSAPP_API_KEY=pitka-satunnainen-avain \
  -e WHATSAPP_DEFAULT_ENGINE=GOWS \
  -e WAHA_DASHBOARD_ENABLED=true -e WAHA_DASHBOARD_USERNAME=admin -e WAHA_DASHBOARD_PASSWORD=vaihda \
  -e TZ=Europe/Helsinki \
  -v waha-sessions:/app/.sessions \
  devlikeapro/waha
```

Avaa WAHA:n hallintapaneeli (`http://WAHA-OSOITE:3000/dashboard`), käynnistä istunto `default` ja yhdistä se puhelimen WhatsAppiin QR-koodilla (*WhatsApp → Linkitetyt laitteet*). Käytä mieluiten erillistä numeroa hälytyksille.

Älä avaa WAHA:n porttia internetiin.

### 2. Ryhmän tunnus

Luo WhatsApp-ryhmä ja lisää siihen WAHA:an linkitetty numero. Hae ryhmän `chatId` (muotoa `120363…@g.us`) WAHA:n Swaggerista: `GET /api/default/groups`.

### 3. Webhook `!tila`-komentoa varten

Aseta istunnon webhook osoittamaan Home Assistantiin, tapahtumana `message.any`:

```
http://HA-OSOITE:8123/api/webhook/<gilles_whatsapp_webhook>
```

Tämän voi tehdä WAHA:n hallintapaneelissa istunnon asetuksista tai Swaggerissa (`PUT /api/sessions/default`, `config.webhooks`). Webhook on HA:ssa `local_only`, joten WAHA:n pitää olla samassa lähiverkossa. WAHA lähettää kaikki tilin viestit; paketti reagoi vain kyseisen ryhmän `!tila`-viestiin eikä tallenna niitä HA:n automaatiojälkiin.

### 4. Home Assistant

1. Kopioi `packages/gilles_whatsapp.yaml` HA:n `packages/`-kansioon (muut Gilles-paketit ja asennusskriptin helperit pitää olla asennettu).
2. Lisää `secrets.yaml`:iin arvot mallin `secrets.example.yaml` mukaan.
3. Vaihda tiedostosta `notify.mobile_app_puhelin` oman puhelimesi ilmoituspalveluksi.
4. Tarkista konfiguraatio ja käynnistä HA uudelleen.

Testaa kirjoittamalla ryhmään `!tila`.
