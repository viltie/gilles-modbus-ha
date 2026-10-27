# Löydökset

> 🇫🇮 **Suomi** · [🇬🇧 English](FINDINGS.en.md)

Täydentää alkuperäisen projektin [rekisterikarttaa](https://github.com/mschabhuettl/gilles-hpk-ra-modbus/blob/main/docs/REGISTER_MAP.md). Arvot on verrattu Touch-paneeliin (VNC) samalla hetkellä, 28.10.2026, kun kattila oli valmiustilassa varaajan ollessa lämmin.

## REG70 = polttoainevaraston lämpötila (×0,1 °C)

| | Arvo |
|---|---|
| Rekisteri | 70, holding, int32 |
| Raaka-arvo | 159 |
| Touch: *Polttoainevaraston lämpötila* | 16 °C |
| Skaalaus | ×0,1 °C → 15,9 °C |

Alkuperäisessä projektissa REG70 on aina ollut 0, joten sen merkitys jäi tuntemattomaksi. Todennäköisin selitys on, ettei siinä asennuksessa ole varastoanturia. Sensori on paketissa [`packages/gilles_local.yaml`](../packages/gilles_local.yaml).

Varmuus: yksi vertailupiste. Arvo on kuitenkin selvästi erillään muista rekistereistä, ja Touch-paneelin Trendi-näkymän tasainen sininen käyrä noin 16–18 asteen kohdalla sopii siihen.

## Tilakoodi 61 = "Varaajan lämpötila saavutettu"

REG46 (`StatusBitmap`) = 61. Samalla hetkellä Touch-paneeli näytti:

- otsikkopalkissa: *Varaajan lämpötila saavutettu*
- alapalkissa: *Varaaja ei kytöä*

Alkuperäinen projekti merkitsi koodin 61 alustavaksi ("Puffertemperatur erreicht?"). Tämä vahvistaa sen.

## Mitä Modbusista ei saa

| Touch-arvo | Tulos |
|---|---|
| Varaajan ylälämpötila (67 °C) | ei löydy |
| Varaajan alalämpötila (66 °C) | ei löydy |
| Paluuveden lämpötila, asetettu (60 °C) | ei löydy |

Menetelmä:

- Holding-rekisterit (FC03) vastaavat vain osoitteissa 0–93. Osoitteesta 94 alkaen ohjain palauttaa virheen.
- Kaikki osoitteet 0–93 luettiin sekä 16- että 32-bittisinä, ja niistä etsittiin arvoja 66/67, 595–605 ja 655–675 (raaka-arvona ja ×10).
- Input-rekisterit (FC04) palauttavat poikkeuksen 01 (*Illegal function*).

Varaajan lämpötilat saa Home Assistantiin vain erillisillä antureilla.

## Touch-paneelin nimet ↔ Home Assistant

Entiteettinimet ovat sellaiset kuin ne ovat asennusskriptin jälkeen (alkuperäisen projektin viitenimet).

| Touch (suomi) | Entiteetti | Rekisteri | Arvo 28.10. |
|---|---|---|---|
| Kattilan lämpötila | `sensor.gilles_kesseltemperatur` | 48 | 71 / 70,8 |
| Savukaasun lämpötila | `sensor.gilles_abgastemperatur` | 50 | 71 / 71,1 |
| Paluuveden lämpötila | `sensor.gilles_rucklauftemperatur` | 52 | 60 / 59,7 |
| O2-arvo | `sensor.gilles_o2_ist` | 54 | 1,0 / 1,0 |
| Ensiöilma | `sensor.gilles_primar_ist_vermutet` | 58 | 0 / 0 |
| Toisioilma | `sensor.gilles_sekundar_ist_vermutet` | 60 | 0 / 0 |
| Savukaasuimuri | `sensor.gilles_saugzug_ist_vermutet` | 62 | 0 / 0 |
| Kattilan tila: *Varaaja / kattila* | `sensor.gilles_boiler_status` (*Puffer/Boiler*) | 44 | 3 |
| Stokerin tila: *Stokeri pois päältä* | `sensor.gilles_brenn_phase` (*Standby*) | 42 | 0 |
| *Varaajan lämpötila saavutettu* | `sensor.gilles_anlagen_zustand` | 46 | 61 |
| Polttoainevaraston lämpötila | `sensor.gilles_polttoainevaraston_lampotila` | 70 | 16 / 15,9 |
| Tuhkanpoisto: *Automaatti odota* | `sensor.gilles_ascheaustragung_aktiv` | 78 | 0 |
| Varaajan ylä- ja alalämpötila | – | – | ei Modbusissa |

Arvo-sarakkeessa on ensin Touch-paneelin lukema ja sitten HA:n lukema.

## Rekisterien tila valmiustilassa

Raaka-arvot (int32) 28.10.2026 klo 00.02. Kattila valmiustilassa, varaaja lämmin. Hyödyllinen vertailukohta, kun omia arvoja tulkitaan.

```
 0:170   2:700   4:400   6:1000  8:300  10:1000 12:800  14:85   16:105  18:220
20:450  22:8    24:200  26:800  28:50   30:30   32:30   34:700  36:1100 38:1800
40:2100 42:0    44:3    46:61   48:708  50:711  52:597  54:10   56:0    58:0
60:0    62:0    64:0    66:1620 68:0    70:159  72:0    74:0    76:0    78:0
80–92: 0
```

## Asennushuomioita

- **Entiteettinimet:** tuoreessa asennuksessa HA muodostaa nimet YAML-nimistä (esim. `foerderschnecke`), mutta helperit ja kojelauta odottavat alkuperäisen asennuksen nimiä (esim. `forderschnecke`, `_vermutet`-päätteet). 17 entiteettiä täytyy nimetä uudelleen. `scripts/gilles_setup.py` tekee sen.
- **`helpers.json`:in `input_number`-helperit** käyttävät kenttiä `min_value`/`max_value` (Home Assistant MCP:n nimeäminen). HA:n websocket-API odottaa kenttiä `min`/`max`. Skripti muuntaa ne.
- **HA 2026.6.2:** kaikki paketit, helperit (myös derivative-helperin `max_sub_interval`) ja automaatiot toimivat, vaikka alkuperäinen projekti on testattu versioilla 2026.9–2026.10.
- **Toinen Modbus-laite:** toimii rinnakkain omassa paketissaan omalla `name:`-arvollaan.
