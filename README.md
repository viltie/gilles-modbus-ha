# Gilles-hakekattila Home Assistantiin (Modbus TCP)

> 🇫🇮 **Suomi** · [🇬🇧 English](README.en.md)

Valmis paketti Gilles-hakekattilan (Touch-paneeli, Sigmatek-ohjain) liittämiseen Home Assistantiin Modbus TCP:n kautta. Mukana on asennusskripti, joka luo kaikki helperit ja automaatiot yhdellä komennolla, Touch-paneelin Trendi-näkymää vastaava kojelauta suomeksi sekä uusia rekisterilöydöksiä.

Pohjana on [mschabhuettl/gilles-hpk-ra-modbus](https://github.com/mschabhuettl/gilles-hpk-ra-modbus) (MIT), jonka rekisterikartta ja HA-paketit ovat tämän repon perusta. Tämä repo lisää siihen:

- **Polttoainevaraston lämpötilan** (REG70) – alkuperäisessä projektissa tuntematon rekisteri
- **Tilakoodin 61 vahvistuksen**: "Varaajan lämpötila saavutettu"
- **Asennusskriptin** (`scripts/gilles_setup.py`), joka tekee alkuperäisen ohjeen käsityövaiheet 4–6 automaattisesti
- **Suomenkielisen trendikojelaudan** (`dashboards/gilles_trend.yaml`)
- **Touch-paneelin suomenkieliset nimet** ↔ HA-entiteetit -taulukon
- Tiedon siitä, **mitä Modbusista ei saa** (varaajan lämpötilat)

Löydökset tarkemmin: [docs/FINDINGS.md](docs/FINDINGS.md).

## Vaatimukset

- Gilles-kattila, jonka Touch-ohjaimessa Modbus TCP on päällä (portti 502)
- Home Assistant 2026.6 tai uudempi (testattu 2026.6.2; alkuperäinen projekti 2026.9–2026.10)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card) (HACS) trendikojelautaa varten

## Asennus

### 1. Paketit

Kopioi `packages/`-hakemiston tiedostot HA:n konfiguraatiohakemiston `packages/`-kansioon:

| Tiedosto | Sisältö |
|---|---|
| `gilles_modbus.yaml` | 40 raakasensoria ja tilatemplatet (alkuperäisestä projektista) |
| `gilles_derived.yaml` | Viimeisimmän käynnistyksen ja tuhkanpoiston aikaleimat (alkuperäisestä projektista) |
| `gilles_local.yaml` | Polttoainevaraston lämpötila (tämä repo) |

Vaihda `gilles_modbus.yaml`:iin kattilasi IP-osoite kohtaan `host: 192.0.2.1`.

Jos paketit eivät ole vielä käytössä, lisää `configuration.yaml`:iin olemassa olevan `homeassistant:`-lohkon alle:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Tiedostonimissä pitää olla alaviiva, ei viivaa. Tarkista konfiguraatio ja käynnistä HA uudelleen.

**Jos sinulla on jo toinen Modbus-laite** (esim. latausasema) omassa paketissaan, se ei haittaa: HA yhdistää pakettien `modbus:`-listat.

### 2. Helperit ja automaatiot

Tee HA:ssa long-lived access token (*Profiili → Turvallisuus → Long-lived access tokens*). Kopioi koko repo HA:n konfiguraatiohakemistoon tai muualle HA-konttiin ja aja:

```bash
docker exec -it homeassistant sh -c \
  'HA_TOKEN=<token> python3 /config/gilles-modbus-ha/scripts/gilles_setup.py --dry'
```

`--dry` näyttää, mitä tehtäisiin. Kun tulos näyttää oikealta, aja sama ilman `--dry`-valitsinta. Skripti:

1. nimeää 17 YAML-entiteettiä alkuperäisen projektin viitenimien mukaisiksi (esim. `sensor.gilles_foerderschnecke_soll` → `sensor.gilles_forderschnecke_soll`), jotta helperit ja kojelauta löytävät ne
2. luo 36 helperiä (`upstream/helpers.json`): tilastot, käyttöajat, laskurit, käynnistyksiä laskevan SQL-sensorin ja diagnostiikan
3. luo 4 automaatiota (`upstream/automations.yaml`), jotka päivittävät laskureita. **Ne eivät koskaan kirjoita kattilaan.**

Skriptin voi ajaa uudelleen: olemassa olevat entiteetit ohitetaan. Se toimii myös HA-kontin ulkopuolella (`--url http://<ha-osoite>:8123`), jos koneella on Python sekä `aiohttp` ja `PyYAML`.

Poista token HA:sta, kun asennus on valmis.

### 3. Kojelaudat

Lisää `configuration.yaml`:iin:

```yaml
lovelace:
  dashboards:
    gilles-kattila:
      mode: yaml
      title: Gilles
      icon: mdi:fire
      show_in_sidebar: true
      filename: dashboards/gilles_trend.yaml
    dashboard-gilles:
      mode: yaml
      title: Gilles Heizung
      icon: mdi:fire-circle
      show_in_sidebar: true
      filename: dashboards/gilles_upstream.yaml
```

ja kopioi `dashboards/gilles_trend.yaml` sekä `upstream/dashboard.yaml` (nimellä `gilles_upstream.yaml`) HA:n `dashboards/`-kansioon. Käynnistä HA uudelleen.

- **Gilles** (tämä repo): Touch-paneelin Trendi-näkymää vastaava 24 tunnin graafi (savukaasu, kattila, paluuvesi, polttoainevarasto, jäännöshappi) ja tilat suomeksi.
- **Gilles Heizung** (alkuperäinen projekti, saksaksi): käyttötilastot, käynnistyslaskurit, diagnostiikka ja parametrit.

## Mitä odottaa asennuksen jälkeen

- Kolme sensoria (`zeit_seit_brennstart`, `zeit_seit_aschenaustragung`, `startphase_minuten`) on tilassa *unavailable*, kunnes poltin käynnistyy ensimmäisen kerran. Tämä on normaalia.
- HA varoittaa lokissa, että `Gilles Brenn Phase Code` luetaan alle 5 sekunnin välein. Tämä on tarkoituksellista: 2 sekunnin lukuväli estää kattilan TCP-yhteyttä katkeamasta (noin 3 sekunnin aikakatkaisu).
- Laskurit alkavat nollasta asennushetkellä.

## Touch-paneelin vertailu

Touch-paneeliin pääsee lähiverkossa VNC:llä (Sigmatek, portti 5925), mikä helpottaa arvojen vertailua HA:han. **Älä avaa VNC- tai Modbus-porttia internetiin**: kummassakaan ei ole tunnistautumista.

## Lisenssi

MIT, katso [LICENSE](LICENSE). Hakemiston `upstream/` sekä tiedostot `packages/gilles_modbus.yaml` ja `packages/gilles_derived.yaml` ovat alkuperäisestä projektista (commit `1b19d56`), ja niihin pätee [upstream/LICENSE](upstream/LICENSE).
