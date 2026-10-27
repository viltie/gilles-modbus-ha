#!/usr/bin/env python3
"""Install the Gilles helpers and automations into Home Assistant through its API.

Does the manual steps 4-6 of the upstream guide in one go:
  * renames the YAML entities to the reference entity IDs (upstream/entity_ids.json)
  * creates the 36 helpers from upstream/helpers.json, in list order
  * creates the four automations from upstream/automations.yaml

Existing entities and automations are skipped, so the script is safe to re-run.

Usage:
  HA_TOKEN=<long-lived token> python3 gilles_setup.py [--url http://127.0.0.1:8123] [--dry]

Requires: aiohttp and PyYAML (both are present inside the Home Assistant container).
"""
import argparse
import asyncio
import json
import os
import re
from pathlib import Path

import aiohttp
import yaml

UPSTREAM = Path(__file__).resolve().parent.parent / "upstream"
STORAGE_HELPERS = {"counter", "input_number", "input_datetime", "input_boolean"}
# helpers.json uses MCP-style field names; the websocket API expects these
WS_KEYS = {"min_value": "min", "max_value": "max"}


class HA:
    def __init__(self, session, url, token):
        self.s, self.url, self.n = session, url.rstrip("/"), 0
        self.hdr = {"Authorization": f"Bearer {token}"}
        self.token = token

    async def connect(self):
        self.ws = await self.s.ws_connect(f"{self.url}/api/websocket")
        await self.ws.receive_json()
        await self.ws.send_json({"type": "auth", "access_token": self.token})
        if (await self.ws.receive_json())["type"] != "auth_ok":
            raise SystemExit("authentication failed - check HA_TOKEN")

    async def call(self, **msg):
        self.n += 1
        msg["id"] = self.n
        await self.ws.send_json(msg)
        while True:
            r = await self.ws.receive_json()
            if r.get("id") == self.n:
                return r

    async def exists(self, entity_id):
        async with self.s.get(f"{self.url}/api/states/{entity_id}", headers=self.hdr) as r:
            return r.status == 200

    async def registry(self):
        return (await self.call(type="config/entity_registry/list"))["result"]

    async def rename(self, cur, new):
        r = await self.call(type="config/entity_registry/update", entity_id=cur, new_entity_id=new)
        print(f"  rename {cur} -> {new}: {'ok' if r['success'] else r.get('error')}")

    async def post(self, path, body):
        async with self.s.post(f"{self.url}{path}", headers=self.hdr, json=body) as r:
            data = await r.json()
            if r.status >= 400:
                raise RuntimeError(f"{r.status}: {data}")
            return data


def form_payload(schema, values):
    """Pick the values a config-flow form asks for, including collapsible sections."""
    out = {}
    for field in schema:
        name = field["name"]
        if field.get("type") == "expandable":
            sub = {**values, **values.get(name, {})}
            inner = {f["name"]: sub[f["name"]] for f in field["schema"] if f["name"] in sub}
            if inner:
                out[name] = inner
        elif name in values:
            out[name] = values[name]
    return out


async def run_flow(ha, domain, values, menu_choice):
    res = await ha.post("/api/config/config_entries/flow", {"handler": domain, "show_advanced_options": True})
    for _ in range(8):
        kind = res.get("type")
        if kind == "create_entry":
            return
        if kind == "abort":
            raise RuntimeError(f"aborted: {res.get('reason')}")
        if kind == "menu":
            body = {"next_step_id": menu_choice}
        elif kind == "form":
            if res.get("errors"):
                raise RuntimeError(f"errors in step {res['step_id']}: {res['errors']}")
            body = form_payload(res["data_schema"], values)
        else:
            raise RuntimeError(f"unexpected flow result: {res}")
        res = await ha.post(f"/api/config/config_entries/flow/{res['flow_id']}", body)
    raise RuntimeError("config flow did not finish")


async def create_helper(ha, p):
    htype = p.get("helper_type") or p.get("domain")
    if htype in STORAGE_HELPERS:
        data = {WS_KEYS.get(k, k): v for k, v in p.items() if k != "helper_type"}
        r = await ha.call(type=f"{htype}/create", **data)
        if not r["success"]:
            raise RuntimeError(r.get("error"))
    else:
        cfg = dict(p.get("config", {}))
        values = {"name": p.get("name", cfg.get("name")), **cfg, **cfg.get("additional_options", {})}
        await run_flow(ha, htype, values, cfg.get("next_step_id"))


async def main(args):
    ref = json.loads((UPSTREAM / "entity_ids.json").read_text())
    helpers = json.loads((UPSTREAM / "helpers.json").read_text())["helpers"]
    automations = yaml.safe_load((UPSTREAM / "automations.yaml").read_text())

    async with aiohttp.ClientSession() as session:
        ha = HA(session, args.url, args.token)
        await ha.connect()

        print("== entity IDs")
        reg = {e["unique_id"]: e["entity_id"] for e in await ha.registry() if e["platform"] in ("modbus", "template")}
        for uid, want in ref["yaml_entities"].items():
            if uid not in reg:
                print(f"  missing {want} - are the packages installed and HA restarted?")
            elif reg[uid] != want:
                print(f"  would rename {reg[uid]} -> {want}") if args.dry else await ha.rename(reg[uid], want)

        print("== helpers")
        failed = 0
        for h in helpers:
            want = h["entity_id"]
            if await ha.exists(want):
                print(f"  skip {want} (exists)")
                continue
            if args.dry:
                print(f"  would create {want}")
                continue
            before = {e["entity_id"] for e in await ha.registry()}
            try:
                await create_helper(ha, h["parameters"])
                await asyncio.sleep(1)
                new = [e["entity_id"] for e in await ha.registry() if e["entity_id"] not in before]
                if new and new[0] != want:
                    await ha.rename(new[0], want)
                print(f"  created {want}")
            except Exception as e:  # report and continue with the rest
                failed += 1
                print(f"  FAIL {want}: {e}")

        print("== automations")
        for a in automations:
            aid = "gilles_" + re.sub(r"[^a-z0-9]+", "_", a["alias"].lower().replace("gilles", "")).strip("_")
            if await ha.exists(f"automation.{aid}"):
                print(f"  skip {aid} (exists)")
                continue
            if args.dry:
                print(f"  would create {aid}")
                continue
            await ha.post(f"/api/config/automation/config/{aid}", {**a, "id": aid})
            print(f"  created {aid}")

        if failed:
            raise SystemExit(f"{failed} helper(s) failed, see above")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default=os.environ.get("HA_URL", "http://127.0.0.1:8123"))
    ap.add_argument("--token", default=os.environ.get("HA_TOKEN"))
    ap.add_argument("--dry", action="store_true", help="show what would be done without changing anything")
    a = ap.parse_args()
    if not a.token:
        ap.error("set HA_TOKEN or pass --token")
    asyncio.run(main(a))
