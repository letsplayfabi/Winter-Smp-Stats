#!/usr/bin/env python3
"""Holt Spielerstatistiken vom exaroton-Server und schreibt docs/stats.json.

Umgebungsvariablen: EXAROTON_TOKEN, EXAROTON_SERVER_ID, optional WORLD_DIR (Standard: world)
Testen ohne API: python fetch_stats.py --local ./testdaten
"""
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.exaroton.com/v1"
WORLD = os.environ.get("WORLD_DIR", "world")
OUT = Path("docs/stats.json")


def remote(path):
    url = f"{API}/servers/{os.environ['EXAROTON_SERVER_ID']}/files/{urllib.parse.quote(path)}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {os.environ['EXAROTON_TOKEN'].strip()}",
        "User-Agent": "mc-stats-site/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} bei {path}: {e.read().decode(errors='replace')[:300]}")
        raise

def load(local):
    """Gibt ({uuid: stats_dict}, {uuid: name}) zurück."""
    if local:
        base = Path(local)
        files = {p.stem: json.loads(p.read_text()) for p in (base / WORLD / "stats").glob("*.json")}
        cache = base / "usercache.json"
        users = json.loads(cache.read_text()) if cache.exists() else []
    else:
        listing = json.loads(remote(f"info/{WORLD}/stats"))["data"].get("children") or []
        files = {}
        for c in listing:
            if c["name"].endswith(".json"):
                files[c["name"][:-5]] = json.loads(remote(f"data/{WORLD}/stats/{c['name']}"))
        try:
            users = json.loads(remote("data/usercache.json"))
        except Exception:
            users = []
    return files, {u["uuid"]: u["name"] for u in users}


def summarize(uuid, raw, names):
    s = raw.get("stats", {})
    c = s.get("minecraft:custom", {})
    ticks = c.get("minecraft:play_time", c.get("minecraft:play_one_minute", 0))
    walked = c.get("minecraft:walk_one_cm", 0) + c.get("minecraft:sprint_one_cm", 0)
    return {
        "uuid": uuid,
        "name": names.get(uuid, uuid[:8]),
        "hours": round(ticks / 20 / 3600, 1),
        "deaths": c.get("minecraft:deaths", 0),
        "mob_kills": c.get("minecraft:mob_kills", 0),
        "blocks_mined": sum(s.get("minecraft:mined", {}).values()),
        "km_walked": round(walked / 100000, 1),
        "jumps": c.get("minecraft:jump", 0),
    }


def main():
    local = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None
    files, names = load(local)
    ov = json.loads(Path("overrides.json").read_text()) if Path("overrides.json").exists() else {}
    po = ov.get("players", {})
    players = []
    for uuid, raw in files.items():
        p = summarize(uuid, raw, names)
        o = po.get(uuid) or po.get(p["name"]) or {}
        if o.get("hidden"):
            continue
        p["display_name"] = o.get("display_name", p["name"])
        p["title"] = o.get("title", "")
        players.append(p)
    players.sort(key=lambda p: p["hours"], reverse=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "site": ov.get("site", {}),
        "players": players,
    }, ensure_ascii=False, indent=1))
    print(f"{len(players)} Spieler geschrieben")


if __name__ == "__main__":
    main()
