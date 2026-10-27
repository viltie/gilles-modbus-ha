# Gilles pellet boiler in Home Assistant (Modbus TCP)

> [🇫🇮 Suomi](README.md) · 🇬🇧 **English**

A ready-to-use package for connecting a Gilles pellet boiler (Touch panel, Sigmatek controller) to Home Assistant over Modbus TCP. It includes an installer script that creates all helpers and automations with one command, a dashboard that mirrors the Touch panel's Trend view, and new register findings.

It builds on [mschabhuettl/gilles-hpk-ra-modbus](https://github.com/mschabhuettl/gilles-hpk-ra-modbus) (MIT), whose register map and HA packages are the foundation of this repository. This repository adds:

- **Fuel store temperature** (REG70), a register listed as unknown upstream
- **Confirmation of status code 61**: "buffer temperature reached"
- **An installer script** (`scripts/gilles_setup.py`) that automates manual steps 4–6 of the upstream guide
- **A trend dashboard** (`dashboards/gilles_trend.yaml`, Finnish labels)
- **A table mapping the Touch panel's Finnish labels** to HA entities
- What is **not available over Modbus** (buffer tank temperatures)

Details: [docs/FINDINGS.en.md](docs/FINDINGS.en.md).

## Requirements

- A Gilles boiler with Modbus TCP enabled on the Touch controller (port 502)
- Home Assistant 2026.6 or newer (tested on 2026.6.2; upstream on 2026.9–2026.10)
- [mini-graph-card](https://github.com/kalkih/mini-graph-card) (HACS) for the trend dashboard

## Installation

### 1. Packages

Copy the files in `packages/` to the `packages/` folder of your HA configuration directory:

| File | Contents |
|---|---|
| `gilles_modbus.yaml` | 40 raw sensors and state templates (upstream) |
| `gilles_derived.yaml` | Timestamps of the last burner start and ash discharge (upstream) |
| `gilles_local.yaml` | Fuel store temperature (this repository) |

Set your boiler's IP address in `gilles_modbus.yaml` (`host: 192.0.2.1`).

If packages are not enabled yet, add this under your existing `homeassistant:` block in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Use underscores, not hyphens, in file names. Check the configuration and restart HA.

**Another Modbus device** (e.g. an EV charger) in its own package is fine: HA merges the `modbus:` lists of all packages.

### 2. Helpers and automations

Create a long-lived access token in HA (*Profile → Security → Long-lived access tokens*). Copy the whole repository into the HA configuration directory or elsewhere inside the HA container and run:

```bash
docker exec -it homeassistant sh -c \
  'HA_TOKEN=<token> python3 /config/gilles-modbus-ha/scripts/gilles_setup.py --dry'
```

`--dry` shows what would be done. When the output looks right, run the same command without `--dry`. The script:

1. renames 17 YAML entities to the upstream reference IDs (e.g. `sensor.gilles_foerderschnecke_soll` → `sensor.gilles_forderschnecke_soll`) so the helpers and dashboard find them
2. creates 36 helpers (`upstream/helpers.json`): statistics, runtimes, counters, an SQL sensor that counts starts, and diagnostics
3. creates 4 automations (`upstream/automations.yaml`) that update the counters. **They never write to the boiler.**

The script can be re-run safely: existing entities are skipped. It also works outside the HA container (`--url http://<ha-host>:8123`) if Python, `aiohttp` and `PyYAML` are installed.

Delete the token in HA when you are done.

### 3. Dashboards

Add to `configuration.yaml`:

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

Copy `dashboards/gilles_trend.yaml` and `upstream/dashboard.yaml` (as `gilles_upstream.yaml`) to the HA `dashboards/` folder and restart HA.

- **Gilles** (this repository): a 24-hour graph matching the Touch panel's Trend view (flue gas, boiler, return water, fuel store, residual oxygen) plus status cards, labelled in Finnish.
- **Gilles Heizung** (upstream, German): operating statistics, start counters, diagnostics and parameters.

## What to expect after installation

- Three sensors (`zeit_seit_brennstart`, `zeit_seit_aschenaustragung`, `startphase_minuten`) stay *unavailable* until the burner's first start. This is normal.
- HA logs a warning that `Gilles Brenn Phase Code` is polled more often than every 5 seconds. This is intentional: the 2-second interval keeps the boiler's TCP connection from timing out (about 3 seconds idle).
- Counters start from zero at installation.

## Comparing with the Touch panel

The Touch panel can be reached on the LAN over VNC (Sigmatek, port 5925), which makes it easy to compare values with HA. **Never expose the VNC or Modbus port to the internet**: neither has authentication.

## License

MIT, see [LICENSE](LICENSE). The `upstream/` directory and the files `packages/gilles_modbus.yaml` and `packages/gilles_derived.yaml` come from the upstream project (commit `1b19d56`) and are covered by [upstream/LICENSE](upstream/LICENSE).
