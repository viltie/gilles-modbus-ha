# Gilles-hakekattila Home Assistantiin (Modbus TCP)

> 🇫🇮 **Suomi** · [🇬🇧 English](README.en.md)

Gilles-hakekattilan (Touch-paneeli, Sigmatek-ohjain) liittäminen Home Assistantiin Modbus TCP:n kautta, **suomeksi**. Repo sisältää:

- asennusskriptin, joka luo kaikki helperit ja automaatiot yhdellä komennolla
- täysin suomenkielisen kojelaudan, jossa on Touch-paneelin Trendi-näkymää vastaava graafi
- uusia rekisterilöydöksiä

Pohjana on [mschabhuettl/gilles-hpk-ra-modbus](https://github.com/mschabhuettl/gilles-hpk-ra-modbus) (MIT). Sen rekisterikartta, Modbus-paketit, helperit ja automaatiot ovat tämän repon perusta, ja alkuperäinen projekti on saksankielinen.

## Mitä tämä repo lisää

- **Polttoainevaraston lämpötila** (REG70). Alkuperäisessä projektissa tämä rekisteri on tuntematon.
- **Tilakoodin 61 vahvistus**: "Varaajan lämpötila saavutettu".
- **Suomenkieliset tilatekstit**: polttovaihe, kattilan tila, laitteiston tila ja asetusarvoprofiili. Sanamuodot noudattavat Touch-paneelia.
- **Suomenkielinen kojelauta** (`dashboards/gilles_fi.yaml`). Siinä ovat kaikki alkuperäisen kojelaudan sivut käännettyinä sekä trendigraafi.
- **Asennusskripti** (`scripts/gilles_setup.py`). Se tekee alkuperäisen ohjeen käsityövaiheet 4–6 automaattisesti.
- **Taulukko Touch-paneelin suomenkielisistä nimistä** ja niitä vastaavista HA-entiteeteistä.
- Tieto siitä, **mitä Modbusista ei saa**: varaajan lämpötiloja.

Löydökset tarkemmin: [docs/FINDINGS.md](docs/FINDINGS.md).

## Kojelauta

| Sivu | Sisältö |
|---|---|
| **Yleiskatsaus** | Trendi 24 h (savukaasu, kattila, paluuvesi, polttoainevarasto, jäännöshappi), lämpötilat, tilat, palaminen, lämpötila- ja O₂-historia |
| **Poltin** | Ensiöilma, toisioilma, savukaasuimuri ja savukaasu suhteessa asetusarvoihin, polttovaiheiden historia |
| **Käyttötilastot** | Käynnistykset (tänään, viikko, kuukausi, yhteensä), käyttöajat, 24 tunnin min/max-arvot, datan laatu, käynnistysdiagnostiikka, säädettävät hälytysrajat |
| **Rekisterit** | Rekisterihavainnot ja tuntemattomien rekisterien historia |
| **Parametrit** | Kattilan, savukaasun, puhaltimien ja tuhkanpoiston asetusarvot (vain luku) |

## Vaatimukset

- Gilles-kattila, jonka Touch-ohjaimessa Modbus TCP on päällä (portti 502)
- Home Assistant 2026.6 tai uudempi (testattu 2026.6.2; alkuperäinen projekti 2026.9–2026.10)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card) (HACS) trendigraafeja varten

## Asennus

### 1. Paketit

Kopioi `packages/`-hakemiston tiedostot HA:n konfiguraatiohakemiston `packages/`-kansioon:

| Tiedosto | Sisältö |
|---|---|
| `gilles_modbus.yaml` | 40 raakasensoria ja tilatemplatet (alkuperäisestä projektista) |
| `gilles_derived.yaml` | Viimeisimmän käynnistyksen ja REG78-signaalin aikaleimat (alkuperäisestä projektista) |
| `gilles_local.yaml` | Polttoainevaraston lämpötila ja suomenkieliset tilatekstit (tämä repo) |

Vaihda `gilles_modbus.yaml`:iin kattilasi IP-osoite kohtaan `host: 192.0.2.1`.

Jos paketit eivät ole vielä käytössä, lisää `configuration.yaml`:iin olemassa olevan `homeassistant:`-lohkon alle:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Tiedostonimissä pitää olla alaviiva, ei viivaa. Tarkista konfiguraatio ja käynnistä HA uudelleen.

Jos sinulla on jo toinen Modbus-laite (esim. latausasema) omassa paketissaan, se ei haittaa: HA yhdistää pakettien `modbus:`-listat.

### 2. Helperit ja automaatiot

Tee HA:ssa long-lived access token (*Profiili → Turvallisuus → Long-lived access tokens*). Kopioi koko repo HA:n konfiguraatiohakemistoon, esimerkiksi `/config/gilles-modbus-ha`, ja aja HA-kontissa:

```bash
docker exec -it homeassistant sh -c \
  'HA_TOKEN=<token> python3 /config/gilles-modbus-ha/scripts/gilles_setup.py --dry'
```

Vaihda `homeassistant` oman HA-konttisi nimeksi. `--dry` näyttää, mitä tehtäisiin. Kun tulos näyttää oikealta, aja sama komento ilman `--dry`-valitsinta. Skripti:

1. nimeää 17 YAML-entiteettiä alkuperäisen projektin viitenimien mukaisiksi (esim. `sensor.gilles_foerderschnecke_soll` → `sensor.gilles_forderschnecke_soll`), jotta helperit ja kojelaudat löytävät ne
2. luo 36 helperiä (`upstream/helpers.json`): tilastot, käyttöajat, laskurit, käynnistyksiä laskevan SQL-sensorin ja diagnostiikan
3. luo 4 automaatiota (`upstream/automations.yaml`), jotka päivittävät laskureita. **Ne eivät koskaan kirjoita kattilaan.**

Skriptin voi ajaa uudelleen: olemassa olevat entiteetit ja automaatiot ohitetaan. Se toimii myös HA-kontin ulkopuolella (`--url http://<ha-osoite>:8123`), jos koneella on Python sekä `aiohttp` ja `PyYAML`.

Poista token HA:sta, kun asennus on valmis.

### 3. Kojelauta

Kopioi `dashboards/gilles_fi.yaml` HA:n konfiguraatiohakemiston `dashboards/`-kansioon ja lisää `configuration.yaml`:iin:

```yaml
lovelace:
  dashboards:
    gilles-kattila:
      mode: yaml
      title: Gilles
      icon: mdi:fire
      show_in_sidebar: true
      filename: dashboards/gilles_fi.yaml
```

Käynnistä HA uudelleen. Kojelauta näkyy sivupalkissa nimellä *Gilles*.

Halutessasi voit lisätä rinnalle myös alkuperäisen saksankielisen kojelaudan (`upstream/dashboard.yaml`) samalla tavalla.

## Asennuksen jälkeen

- Kolme sensoria (`zeit_seit_brennstart`, `zeit_seit_aschenaustragung`, `startphase_minuten`) on tilassa *unavailable*, kunnes poltin käynnistyy ensimmäisen kerran. Tämä on normaalia.
- HA varoittaa lokissa, että `Gilles Brenn Phase Code` luetaan alle 5 sekunnin välein. Tämä on tarkoituksellista: 2 sekunnin lukuväli estää kattilan TCP-yhteyttä katkeamasta (noin 3 sekunnin aikakatkaisu).
- Laskurit alkavat nollasta asennushetkellä.
- Graafit täyttyvät vähitellen, kun historiaa kertyy.

## Touch-paneelin vertailu

Touch-paneeliin pääsee lähiverkossa VNC:llä (Sigmatek, portti 5925), mikä helpottaa arvojen vertailua HA:han. **Älä avaa VNC- tai Modbus-porttia internetiin**: kummassakaan ei ole tunnistautumista.

## Lisenssi

MIT, katso [LICENSE](LICENSE). Hakemisto `upstream/` sekä tiedostot `packages/gilles_modbus.yaml` ja `packages/gilles_derived.yaml` ovat alkuperäisestä projektista (commit `1b19d56`), ja niihin pätee [upstream/LICENSE](upstream/LICENSE). Suomenkielisen kojelaudan selitetekstit on käännetty alkuperäisestä kojelaudasta.
