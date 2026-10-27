# Gilles wood chip boiler in Home Assistant (Modbus TCP)

> [🇫🇮 Suomi](README.md) · 🇬🇧 **English**

Connects a Gilles wood chip boiler (Touch panel, Sigmatek controller) to Home Assistant over Modbus TCP, **with a Finnish user interface**. The repository contains:

- an installer script that creates all helpers and automations with one command
- a fully Finnish dashboard, including a graph that mirrors the Touch panel's Trend view
- new register findings

It builds on [mschabhuettl/gilles-hpk-ra-modbus](https://github.com/mschabhuettl/gilles-hpk-ra-modbus) (MIT). Its register map, Modbus packages, helpers and automations are the foundation of this repository; the upstream project is in German.

## What this repository adds

- **Fuel store temperature** (REG70). Upstream lists this register as unknown.
- **Confirmation of status code 61**: "buffer temperature reached".
- **Finnish status texts** for burner phase, boiler mode, system status and setpoint profile, worded like the Finnish Touch panel.
- **A Finnish dashboard** (`dashboards/gilles_fi.yaml`) with every upstream dashboard view translated, plus a trend graph.
- **An installer script** (`scripts/gilles_setup.py`) that automates manual steps 4–6 of the upstream guide.
- **A table mapping the Touch panel's Finnish labels** to HA entities.
- What is **not available over Modbus**: the buffer tank temperatures.

Details: [docs/FINDINGS.en.md](docs/FINDINGS.en.md).

## Dashboard

| View | Contents |
|---|---|
| **Yleiskatsaus** (overview) | 24 h trend (flue gas, boiler, return water, fuel store, residual oxygen), temperatures, status, combustion, temperature and O₂ history |
| **Poltin** (burner) | Primary air, secondary air, induced-draught fan and flue gas against their setpoints, burner phase history |
| **Käyttötilastot** (statistics) | Starts (today, week, month, total), runtimes, 24 h min/max, data quality, start diagnostics, adjustable alert thresholds |
| **Rekisterit** (registers) | Register findings and history of unidentified registers |
| **Parametrit** (parameters) | Boiler, flue gas, fan and ash removal setpoints (read only) |

## Requirements

- A Gilles boiler with Modbus TCP enabled on the Touch controller (port 502)
- Home Assistant 2026.6 or newer (tested on 2026.6.2; upstream on 2026.9–2026.10)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card) (HACS) for the trend graphs

## Installation

### 1. Packages

Copy the files in `packages/` to the `packages/` folder of your HA configuration directory:

| File | Contents |
|---|---|
| `gilles_modbus.yaml` | 40 raw sensors and state templates (upstream) |
| `gilles_derived.yaml` | Timestamps of the last burner start and REG78 signal (upstream) |
| `gilles_local.yaml` | Fuel store temperature and Finnish status texts (this repository) |

Set your boiler's IP address in `gilles_modbus.yaml` (`host: 192.0.2.1`).

If packages are not enabled yet, add this under your existing `homeassistant:` block in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Use underscores, not hyphens, in file names. Check the configuration and restart HA.

Another Modbus device (e.g. an EV charger) in its own package is fine: HA merges the `modbus:` lists of all packages.

### 2. Helpers and automations

Create a long-lived access token in HA (*Profile → Security → Long-lived access tokens*). Copy the whole repository into the HA configuration directory, for example `/config/gilles-modbus-ha`, and run inside the HA container:

```bash
docker exec -it homeassistant sh -c \
  'HA_TOKEN=<token> python3 /config/gilles-modbus-ha/scripts/gilles_setup.py --dry'
```

Replace `homeassistant` with the name of your HA container. `--dry` shows what would be done. When the output looks right, run the same command without `--dry`. The script:

1. renames 17 YAML entities to the upstream reference IDs (e.g. `sensor.gilles_foerderschnecke_soll` → `sensor.gilles_forderschnecke_soll`) so the helpers and dashboards find them
2. creates 36 helpers (`upstream/helpers.json`): statistics, runtimes, counters, an SQL sensor that counts starts, and diagnostics
3. creates 4 automations (`upstream/automations.yaml`) that update the counters. **They never write to the boiler.**

The script can be re-run safely: existing entities and automations are skipped. It also works outside the HA container (`--url http://<ha-host>:8123`) if Python, `aiohttp` and `PyYAML` are installed.

Delete the token in HA when you are done.

### 3. Dashboard

Copy `dashboards/gilles_fi.yaml` to the `dashboards/` folder of your HA configuration directory and add to `configuration.yaml`:

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

Restart HA. The dashboard appears in the sidebar as *Gilles*.

You can also add the upstream German dashboard (`upstream/dashboard.yaml`) alongside it in the same way.

## After installation

- Three sensors (`zeit_seit_brennstart`, `zeit_seit_aschenaustragung`, `startphase_minuten`) stay *unavailable* until the burner's first start. This is normal.
- HA logs a warning that `Gilles Brenn Phase Code` is polled more often than every 5 seconds. This is intentional: the 2-second interval keeps the boiler's TCP connection from timing out (about 3 seconds idle).
- Counters start from zero at installation.
- Graphs fill in gradually as history accumulates.

## Comparing with the Touch panel

The Touch panel can be reached on the LAN over VNC (Sigmatek, port 5925), which makes it easy to compare values with HA. **Never expose the VNC or Modbus port to the internet**: neither has authentication.

## License

MIT, see [LICENSE](LICENSE). The `upstream/` directory and the files `packages/gilles_modbus.yaml` and `packages/gilles_derived.yaml` come from the upstream project (commit `1b19d56`) and are covered by [upstream/LICENSE](upstream/LICENSE). The explanatory texts in the Finnish dashboard are translated from the upstream dashboard.
