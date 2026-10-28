#!/usr/bin/env python3
"""Holt Spielerstatistiken von exaroton und schreibt docs/stats.json + docs/history.json.
Test ohne API: python fetch_stats.py --local ./testdaten"""
import json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

API = "https://api.exaroton.com/v1"
WORLD = os.environ.get("WORLD_DIR", "world")
D = Path("docs")


def get(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30) as r:
        return r.read()


def remote(path):
    url = f"{API}/servers/{os.environ['EXAROTON_SERVER_ID']}/files/{urllib.parse.quote(path)}"
    h = {"Authorization": f"Bearer {os.environ['EXAROTON_TOKEN'].strip()}", "User-Agent": "mc-stats-site/1.0"}
    try:
        return get(url, h)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} bei {path}: {e.read().decode(errors='replace')[:300]}")
        raise


def load(local):
    dirs = [f"{WORLD}/players/stats", f"{WORLD}/stats"]  # ab 26.1 / davor
    if local:
        b = Path(local)
        d = next((b / x for x in dirs if (b / x).is_dir() and any((b / x).glob("*.json"))), b / dirs[0])
        files = {p.stem: json.loads(p.read_text()) for p in d.glob("*.json")}
        c = b / "usercache.json"
        users = json.loads(c.read_text()) if c.exists() else []
    else:
        x, children = dirs[0], []
        for x in dirs:
            try:
                children = json.loads(remote(f"info/{x}"))["data"].get("children") or []
            except urllib.error.HTTPError:
                continue
            print(f"{len(children)} Einträge in {x}")
            if any(c["name"].endswith(".json") for c in children):
                break
        files = {c["name"][:-5]: json.loads(remote(f"data/{x}/{c['name']}"))
                 for c in children if c["name"].endswith(".json")}
        try:
            users = json.loads(remote("data/usercache.json"))
        except Exception as e:
            print("usercache.json nicht lesbar:", e)
            users = []
    return files, {u["uuid"].lower(): u["name"] for u in users}


def mojang(uuid):
    try:
        return json.loads(get("https://sessionserver.mojang.com/session/minecraft/profile/" + uuid.replace("-", "")))["name"]
    except Exception:
        return None


def summarize(uuid, raw, name):
    s = raw.get("stats", {})
    c, m, k = (s.get(x, {}) for x in ("minecraft:custom", "minecraft:mined", "minecraft:killed"))
    travel = {x[10:-7]: round(v / 100000, 1) for x, v in c.items()
              if x.endswith("_one_cm") and x != "minecraft:fall_one_cm" and v}
    top = lambda d, n=8: [[a[10:], b] for a, b in sorted(d.items(), key=lambda t: -t[1])[:n]]
    return {
        "uuid": uuid, "name": name,
        "hours": round(c.get("minecraft:play_time", c.get("minecraft:play_one_minute", 0)) / 72000, 1),
        "deaths": c.get("minecraft:deaths", 0),
        "mob_kills": c.get("minecraft:mob_kills", 0),
        "blocks_mined": sum(m.values()),
        "diamonds": m.get("minecraft:diamond_ore", 0) + m.get("minecraft:deepslate_diamond_ore", 0),
        "km_travelled": round(sum(travel.values()), 1),
        "jumps": c.get("minecraft:jump", 0),
        "travel": travel, "top_mobs": top(k), "top_blocks": top(m),
    }


def main():
    local = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None
    files, names = load(local)
    players = [summarize(u, raw, names.get(u.lower()) or mojang(u) or u[:8]) for u, raw in files.items()]
    print(f"{len(players)} Spieler, Namen: {[p['name'] for p in players]}")

    D.mkdir(exist_ok=True)
    hp = D / "history.json"
    hist = json.loads(hp.read_text()) if hp.exists() else {}
    today = datetime.now(timezone.utc).date()
    hist[today.isoformat()] = {p["uuid"]: p["hours"] for p in players}
    for d in sorted(hist)[:-60]:
        del hist[d]
    old = [d for d in sorted(hist) if d <= (today - timedelta(days=7)).isoformat()]
    base = hist[old[-1] if old else sorted(hist)[0]]
    for p in players:
        p["week_hours"] = round(max(p["hours"] - base.get(p["uuid"], 0), 0), 1)
    hp.write_text(json.dumps(hist))

    players.sort(key=lambda p: p["hours"], reverse=True)
    (D / "stats.json").write_text(json.dumps(
        {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "players": players},
        ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
