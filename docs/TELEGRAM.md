# Gilles-hälytykset Telegramiin

> 🇫🇮 **Suomi** · [🇬🇧 English](TELEGRAM.en.md)

`packages/gilles_telegram.yaml` lähettää kattilan hälytykset Telegram-ryhmään tai yksityisviestinä ja vastaa komentoon **`/tila`** (tai `!tila`). Viestit kulkevat Home Assistantin oman [Telegram bot -integraation](https://www.home-assistant.io/integrations/telegram_bot/) kautta. Paketti vain lukee kattilan tietoja, se ei kirjoita kattilalle mitään.

**Telegram on suositeltu tapa.** Se on ilmainen, käyttää Telegramin virallista bottirajapintaa, ei vaadi erillistä puhelinnumeroa eikä SIM-korttia, eikä Home Assistantia tarvitse avata internetiin. WhatsApp-hälytykset ([WHATSAPP.md](WHATSAPP.md)) kulkevat epävirallisen WAHA-sillan kautta, joka tarvitsee oman WhatsApp-numeron ja voi katketa. Kanavia voi käyttää myös rinnakkain.

## Hälytykset

Hälytysautomaatiot ovat paketissa `gilles_halytykset.yaml`, ja ne lähettävät jokaiseen asennettuun kanavaan.

| Hälytys | Milloin |
|---|---|
| 🔴 Yhteys kattilaan poikki | Modbus-data puuttuu yli 10 min; ilmoitus myös, kun yhteys palaa |
| 🟠 Sytytysvaihe liian pitkä | `binary_sensor.gilles_startphase_zu_lang` (raja säädettävissä kojelaudalta) |
| 🟠 Lämpötila ei nouse käynnistyksen jälkeen | `binary_sensor.gilles_temperaturanstieg_fehlt` yli 25 min (normaalikäytössä tämä menee päälle lyhyesti, siksi pitkä viive) |
| 🟠 Tiheät käynnistykset | käynnistyksiä 24 h yli rajan, korkeintaan kerran 12 h:ssa |
| 🟠 / 🔴 Käynnistys keskeytyi / kattila sammui | tilakoodi 31 (käynnistys keskeytyi) tai 34 (todennäköisesti "Ei tulta") – näitä ei ole alkuperäisessä projektissa |
| 🔴 Kattila jäähtyy | kattilan lämpötila alle 50 °C yli 15 min |

**`/tila`** vastaa hetken tilanteella: polttovaihe, kattilan ja laitteiston tila, kattila-, savukaasu- ja paluuveden lämpötila, jäännöshappi, polttoainevaraston lämpötila ja käynnistykset 24 h. Paketti vastaa vain `secrets.yaml`:iin määriteltyyn chattiin ja korkeintaan kerran 30 sekunnissa.

Jos Telegram-lähetys epäonnistuu, sama viesti lähetetään puhelimen HA-ilmoituksena.

## Asennus

Vaatimuksena Home Assistant 2026.6 tai uudempi.

### 1. Botti BotFatherilla

1. Avaa Telegramissa [@BotFather](https://t.me/BotFather) ja lähetä `/newbot`.
2. Anna botille nimi ja käyttäjätunnus (päättyy `bot`, esim. `KattilaGillesBot`).
3. BotFather antaa **API-tunnuksen** (`123456789:AA…`). Pidä se salassa.

### 2. Integraatio Home Assistantiin

1. *Asetukset → Laitteet ja palvelut → Lisää integraatio → Telegram bot*.
2. **Platform: Polling.** Se hakee viestit itse Telegramista, joten HA:ta ei tarvitse avata internetiin. (*Broadcast* ei vastaanota viestejä, jolloin `/tila` ei toimi. *Webhooks* vaatii julkisen HTTPS-osoitteen.)
3. **API key**: BotFatherin antama tunnus. Muut kentät voi jättää oletuksiksi.

### 3. Chat ID

Botti lähettää ja vastaanottaa vain sallituissa chateissa, joten tarvitset chatin tunnuksen (chat ID). Yksityischatin tunnus on positiivinen, ryhmän negatiivinen (supergroupilla muotoa `-100…`).

**Yksityisviesteinä:** avaa chat omaan bottiisi ja lähetä `/start` (botti ei voi aloittaa keskustelua itse).

**Ryhmään:** luo Telegram-ryhmä, lisää siihen perheenjäsenet ja botti, ja kirjoita ryhmään `/start`.

Tunnuksen saa helpoimmin Home Assistantin lokista: kun sallimaton chat lähettää botille viestin, integraatio kirjaa virheen *"Unauthorized update - neither user id … nor chat id … is in allowed chats"*. Katso se kohdasta *Asetukset → Järjestelmä → Lokit*; `chat id` on haettu tunnus. Yksityischatissa tunnuksen kertoo myös esimerkiksi [@id_bot](https://t.me/id_bot).

### 4. Salli chat

*Asetukset → Laitteet ja palvelut → Telegram bot*, botin rivin kolmen pisteen valikko → **Add allowed chat ID** → syötä tunnus.

### 5. Paketit ja secrets

1. Kopioi `packages/gilles_halytykset.yaml` ja `packages/gilles_telegram.yaml` HA:n `packages/`-kansioon (muut Gilles-paketit ja asennusskriptin helperit pitää olla asennettu).
2. Lisää `secrets.yaml`:iin sama tunnus:
   ```yaml
   gilles_telegram_chat_id: -1001234567890
   ```
   Useampaan chattiin: `gilles_telegram_chat_id: [-1001234567890, 123456789]` (kaikki pitää olla sallittuja vaiheessa 4).
3. Vaihda `gilles_halytykset.yaml`:sta `notify.mobile_app_puhelin` oman puhelimesi ilmoituspalveluksi.
4. Tarkista konfiguraatio ja käynnistä HA uudelleen.

Testaa kirjoittamalla chattiin `/tila`. Hälytyskanavan voi testata myös *Kehittäjätyökalut → Toiminnot*: `script.gilles_halytys`, `message: testi`.

## Ryhmät ja yksityisyystila

Telegram-boteilla on oletuksena **privacy mode** päällä. Silloin botti näkee ryhmässä vain sille osoitetut komennot (`/tila@KattilaGillesBot`), yleiset komennot (`/tila`), jos se on viimeisin ryhmään kirjoittanut botti, sekä vastaukset omiin viesteihinsä. Kun ryhmässä ei ole muita botteja, `/tila` toimii siis aina, mutta `!tila` vain, jos yksityisyystila on pois päältä:

- BotFather → `/setprivacy` → valitse botti → **Disable**, ja poista botti ryhmästä ja lisää se uudelleen (muutos tulee voimaan vasta silloin).
- Vaihtoehtoisesti tee botista ryhmän ylläpitäjä.

Ilman yksityisyystilaa botti vastaanottaa kaikki ryhmän viestit. Paketti reagoi niistä vain tila-komentoon eikä tallenna niitä HA:n automaatiojälkiin.

Komennon voi lisätä botin valikkoon: BotFather → `/setcommands` → `tila - Kattilan tila nyt`.

Jos tavallinen ryhmä muuttuu supergroupiksi (esim. kun ryhmälle annetaan ylläpitäjiä), sen chat ID vaihtuu. Lisää silloin uusi tunnus sallituksi ja päivitä `secrets.yaml`.

## Useampi botti

Jos HA:ssa on useampi Telegram-botti, lisää skriptin `gilles_telegram_viesti` lähetykseen `config_entry_id:` (botin integraatiomerkinnän tunnus), muuten HA ei tiedä, mitä bottia käyttää. `/tila`-vastaus käyttää automaattisesti bottia, joka sai komennon.
