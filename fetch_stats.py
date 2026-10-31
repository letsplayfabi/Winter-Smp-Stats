#!/usr/bin/env python3
"""Holt Spielerstatistiken von exaroton und schreibt docs/stats.json + docs/history.json.
Test ohne API: python fetch_stats.py --local ./testdaten"""
import json, os, sys, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

API = "https://api.exaroton.com/v1"
D = Path("docs")


STATES = {0: "offline", 1: "online", 2: "starting", 3: "stopping", 4: "restarting", 5: "saving", 6: "loading", 7: "crashed", 8: "pending", 9: "preparing"}


def server_info(sid):
    h = {"Authorization": f"Bearer {os.environ['EXAROTON_TOKEN'].strip()}", "User-Agent": "mc-stats-site/1.0"}
    return json.loads(get(f"{API}/servers/{sid}", h))["data"]


def get(url, headers=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30) as r:
        return r.read()


def remote(sid, path):
    url = f"{API}/servers/{sid}/files/{urllib.parse.quote(path)}"
    h = {"Authorization": f"Bearer {os.environ['EXAROTON_TOKEN'].strip()}", "User-Agent": "mc-stats-site/1.0"}
    try:
        return get(url, h)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"HTTP {e.code} bei {path}: {e.read().decode(errors='replace')[:300]}")
        raise


def level_name(sid):
    """Liest den Namen des Welt-Ordners aus der server.properties."""
    try:
        for line in remote(sid, "data/server.properties").decode(errors="replace").splitlines():
            if line.startswith("level-name="):
                return line.split("=", 1)[1].strip() or "world"
    except Exception as e:
        print("server.properties nicht lesbar:", e)
    return "world"


def load(local, sid, worlds):
    dirs = [f"{w}/{sub}" for w in worlds for sub in ("players/stats", "stats")]  # players/stats ab 26.1
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
                children = (json.loads(remote(sid, f"info/{x}")).get("data") or {}).get("children") or []
            except Exception:
                print(f"  {x}: nicht vorhanden")
                children = []
                continue
            print(f"  {x}: {len(children)} Einträge")
            if any(c["name"].endswith(".json") for c in children):
                break
        files = {c["name"][:-5]: json.loads(remote(sid, f"data/{x}/{c['name']}"))
                 for c in children if c["name"].endswith(".json")}
        try:
            users = json.loads(remote(sid, "data/usercache.json"))
        except Exception as e:
            print("usercache.json nicht lesbar:", e)
            users = []
    if not files:
        print("  WARNUNG: keine Statistik-Dateien gefunden – stimmt der Welt-Ordner? (Eintrag \"world\" in servers.json)")
    return files, {u["uuid"].lower(): u["name"] for u in users}


def mojang(uuid):
    try:
        return json.loads(get("https://sessionserver.mojang.com/session/minecraft/profile/" + uuid.replace("-", "")))["name"]
    except Exception:
        return None


def summarize(uuid, raw, name):
    s = raw.get("stats", {})
    c, m, k, u, kb = (s.get(x, {}) for x in ("minecraft:custom", "minecraft:mined", "minecraft:killed", "minecraft:used", "minecraft:killed_by"))
    ticks = c.get("minecraft:play_time", c.get("minecraft:play_one_minute", 0))
    travel = {x[10:-7]: round(v / 100000, 1) for x, v in c.items()
              if x.endswith("_one_cm") and x != "minecraft:fall_one_cm" and v}
    top = lambda d, n=8: [[a[10:], b] for a, b in sorted(d.items(), key=lambda t: -t[1])[:n]]
    deaths = c.get("minecraft:deaths", 0)
    return {
        "uuid": uuid, "name": name,
        "minutes": round(ticks / 1200), "hours": round(ticks / 72000, 1),
        "deaths": deaths,
        "mob_kills": c.get("minecraft:mob_kills", 0),
        "player_kills": c.get("minecraft:player_kills", 0),
        "entities_killed": sum(k.values()),
        "items_used": sum(u.values()),
        "damage": round(c.get("minecraft:damage_dealt", 0) / 10),
        "blocks_mined": sum(m.values()),
        "diamonds": m.get("minecraft:diamond_ore", 0) + m.get("minecraft:deepslate_diamond_ore", 0),
        "km_travelled": round(sum(travel.values()), 1),
        "jumps": c.get("minecraft:jump", 0),
        "travel": travel, "top_mobs": top(k), "top_blocks": top(m), "top_used": top(u),
        "death_causes": top(kb, 5), "death_other": max(deaths - sum(kb.values()), 0),
        "x": {"debris": m.get("minecraft:ancient_debris", 0), "creepers": k.get("minecraft:creeper", 0),
              "netherrack": m.get("minecraft:netherrack", 0), "deepslate": m.get("minecraft:deepslate", 0),
              "aviate_km": round(c.get("minecraft:aviate_one_cm", 0) / 100000, 1)},
    }


def process(sv, local, first):
    sid = os.environ.get(sv["env"], "").strip()
    if not sid and not local:
        print(f"Überspringe {sv['name']}: Secret {sv['env']} fehlt")
        return
    base = local and (str(Path(local) / sv["key"]) if (Path(local) / sv["key"]).is_dir() else local)
    w = sv.get("world") or os.environ.get("WORLD_DIR") or ("world" if local else level_name(sid))
    worlds = list(dict.fromkeys([w, "world"]))
    print(f"{sv['name']}: suche Statistiken in Welt-Ordner {worlds}")
    files, names = load(base, sid, worlds)
    players = [summarize(u, raw, names.get(u.lower()) or mojang(u) or u[:8]) for u, raw in files.items()]
    print(f"{sv['name']}: {len(players)} Spieler, Namen: {[p['name'] for p in players]}")
    out = D / "data" / sv["key"]
    out.mkdir(parents=True, exist_ok=True)
    hp = out / "history.json"
    if first and not hp.exists() and (D / "history.json").exists():
        hp.write_text((D / "history.json").read_text())
    hist = json.loads(hp.read_text()) if hp.exists() else {}
    today = datetime.now(timezone.utc).date()
    hist[today.isoformat()] = {p["uuid"]: p["hours"] for p in players}
    for d in sorted(hist)[:-60]:
        del hist[d]
    old = [d for d in sorted(hist) if d <= (today - timedelta(days=7)).isoformat()]
    base_h = hist[old[-1] if old else sorted(hist)[0]]
    for p in players:
        p["week_hours"] = round(max(p["hours"] - base_h.get(p["uuid"], 0), 0), 1)
    hp.write_text(json.dumps(hist))
    players.sort(key=lambda p: p["hours"], reverse=True)
    status = {}
    if not local:
        try:
            info = server_info(sid)
            pl = info.get("players") or {}
            status = {"state": STATES.get(info.get("status"), "unknown"), "count": pl.get("count", 0), "max": pl.get("max", 0),
                      "list": pl.get("list") or [], "address": info.get("address", ""),
                      "checked": datetime.now(timezone.utc).isoformat(timespec="minutes")}
        except Exception as e:
            print("Status nicht lesbar:", e)
    (out / "stats.json").write_text(json.dumps(
        {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "players": players, "status": status},
        ensure_ascii=False, indent=1))


def main():
    local = sys.argv[sys.argv.index("--local") + 1] if "--local" in sys.argv else None
    sp = Path("servers.json")
    servers = json.loads(sp.read_text()) if sp.exists() else [{"key": "winter", "name": "Winter SMP", "env": "EXAROTON_SERVER_ID"}]
    D.mkdir(exist_ok=True)
    failed = []
    for i, sv in enumerate(servers):
        try:
            process(sv, local, i == 0)
        except Exception as e:
            print(f"FEHLER bei {sv['name']}: {e}")
            failed.append(sv["name"])
    ok = [{"key": s["key"], "name": s["name"], "extra": s.get("extra", []), "hide": s.get("hide", [])} for s in servers if (D / "data" / s["key"] / "stats.json").exists()]
    (D / "servers.json").write_text(json.dumps(ok, ensure_ascii=False))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
