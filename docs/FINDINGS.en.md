# Findings

> [🇫🇮 Suomi](FINDINGS.md) · 🇬🇧 **English**

Complements the upstream [register map](https://github.com/mschabhuettl/gilles-hpk-ra-modbus/blob/main/docs/REGISTER_MAP.en.md). Values were compared with the Touch panel (over VNC) at the same moment on 2026-10-28, with the boiler in standby and the buffer tank hot.

## REG70 = fuel store temperature (×0.1 °C)

| | Value |
|---|---|
| Register | 70, holding, int32 |
| Raw value | 159 |
| Touch: *Polttoainevaraston lämpötila* (fuel store temperature) | 16 °C |
| Scale | ×0.1 °C → 15.9 °C |

Upstream has only ever seen 0 in REG70, so its meaning was unknown. The most likely explanation is that the upstream installation has no fuel store sensor. The sensor is in [`packages/gilles_local.yaml`](../packages/gilles_local.yaml).

Confidence: one comparison point. The value is clearly distinct from every other register, and it matches the flat blue curve around 16–18 °C in the Touch panel's Trend view.

## Status code 61 = "buffer temperature reached"

REG46 (`StatusBitmap`) = 61. At the same moment the Touch panel showed:

- title bar: *Varaajan lämpötila saavutettu* (buffer temperature reached)
- bottom bar: *Varaaja ei kytöä* (buffer does not need firing)

Upstream marked code 61 as provisional ("Puffertemperatur erreicht?"). This confirms it.

## Not available over Modbus

| Touch value | Result |
|---|---|
| Buffer top temperature (67 °C) | not found |
| Buffer bottom temperature (66 °C) | not found |
| Return water temperature setpoint (60 °C) | not found |

Method:

- Holding registers (FC03) respond only at addresses 0–93. From address 94 on, the controller returns an error.
- Every address 0–93 was read both as 16-bit and as 32-bit values and searched for 66/67, 595–605 and 655–675 (raw and ×10).
- Input registers (FC04) return exception 01 (*Illegal function*).

Buffer tank temperatures can only be brought into Home Assistant with separate sensors.

## Touch panel labels (Finnish) ↔ Home Assistant

Entity IDs as they are after the installer script (upstream reference IDs).

| Touch (Finnish) | English | Entity | Register | Value 2026-10-28 |
|---|---|---|---|---|
| Kattilan lämpötila | Boiler temperature | `sensor.gilles_kesseltemperatur` | 48 | 71 / 70.8 |
| Savukaasun lämpötila | Flue gas temperature | `sensor.gilles_abgastemperatur` | 50 | 71 / 71.1 |
| Paluuveden lämpötila | Return water temperature | `sensor.gilles_rucklauftemperatur` | 52 | 60 / 59.7 |
| O2-arvo | Residual oxygen | `sensor.gilles_o2_ist` | 54 | 1.0 / 1.0 |
| Ensiöilma | Primary air | `sensor.gilles_primar_ist_vermutet` | 58 | 0 / 0 |
| Toisioilma | Secondary air | `sensor.gilles_sekundar_ist_vermutet` | 60 | 0 / 0 |
| Savukaasuimuri | Induced-draught fan | `sensor.gilles_saugzug_ist_vermutet` | 62 | 0 / 0 |
| Kattilan tila: *Varaaja / kattila* | Mode: buffer/boiler | `sensor.gilles_boiler_status` (*Puffer/Boiler*) | 44 | 3 |
| Stokerin tila: *Stokeri pois päältä* | Stoker off | `sensor.gilles_brenn_phase` (*Standby*) | 42 | 0 |
| *Varaajan lämpötila saavutettu* | Buffer temperature reached | `sensor.gilles_anlagen_zustand` | 46 | 61 |
| Polttoainevaraston lämpötila | Fuel store temperature | `sensor.gilles_polttoainevaraston_lampotila` | 70 | 16 / 15.9 |
| Tuhkanpoisto: *Automaatti odota* | Ash removal: automatic, waiting | `sensor.gilles_ascheaustragung_aktiv` | 78 | 0 |
| Varaajan ylä-/alalämpötila | Buffer top/bottom temperature | – | – | not on Modbus |

The value column shows the Touch reading first, then the HA reading.

## Register snapshot in standby

Raw values (int32) on 2026-10-28 at 00:02, boiler in standby, buffer hot. Useful as a reference when interpreting your own values.

```
 0:170   2:700   4:400   6:1000  8:300  10:1000 12:800  14:85   16:105  18:220
20:450  22:8    24:200  26:800  28:50   30:30   32:30   34:700  36:1100 38:1800
40:2100 42:0    44:3    46:61   48:708  50:711  52:597  54:10   56:0    58:0
60:0    62:0    64:0    66:1620 68:0    70:159  72:0    74:0    76:0    78:0
80–92: 0
```

## Installation notes

- **Entity IDs:** on a fresh installation HA derives IDs from the YAML names (e.g. `foerderschnecke`), but the helpers and dashboard expect the upstream installation's IDs (e.g. `forderschnecke`, `_vermutet` suffixes). 17 entities need renaming. `scripts/gilles_setup.py` does this.
- **`input_number` helpers in `helpers.json`** use `min_value`/`max_value` (Home Assistant MCP naming). HA's websocket API expects `min`/`max`. The script converts them.
- **HA 2026.6.2:** all packages, helpers (including the derivative helper's `max_sub_interval`) and automations work, although upstream was validated on 2026.9–2026.10.
- **Another Modbus device:** works side by side in its own package with its own `name:`.
