#!/usr/bin/env python3
"""Holt Spielerstatistiken von exaroton und schreibt docs/stats.json + docs/history.json.
Test ohne API: python fetch_stats.py --local ./testdaten"""
import base64, json, os, random, re, sys, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import challenges as CH

API = "https://api.exaroton.com/v1"
D = Path("docs")
SKINS = D / "skins"


FOOD = set("""apple golden_apple enchanted_golden_apple bread carrot golden_carrot potato baked_potato poisonous_potato beetroot beetroot_soup
melon_slice sweet_berries glow_berries cookie pumpkin_pie mushroom_stew rabbit_stew suspicious_stew beef cooked_beef porkchop cooked_porkchop
mutton cooked_mutton chicken cooked_chicken cod cooked_cod salmon cooked_salmon tropical_fish pufferfish rabbit cooked_rabbit rotten_flesh
spider_eye dried_kelp chorus_fruit honey_bottle milk_bucket""".split())
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


def jl(p, default):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


def skin(uuid, prev):
    """Holt den aktuellen Skin direkt von Mojang und legt ihn unter docs/skins/<hash>.png ab.
    Neuer Skin = neuer Dateiname, deshalb gibt es keine Cache-Probleme auf der Seite."""
    try:
        j = json.loads(get("https://sessionserver.mojang.com/session/minecraft/profile/" + uuid.replace("-", "")))
        tex = next(p["value"] for p in j.get("properties", []) if p.get("name") == "textures")
        sk = (json.loads(base64.b64decode(tex)).get("textures") or {}).get("SKIN")
        if not sk:
            return {"skin": "", "slim": False}
        h = sk["url"].rstrip("/").split("/")[-1]
        if not re.fullmatch(r"[0-9a-f]{16,80}", h):
            raise ValueError("unerwartete Skin-Adresse")
        f = SKINS / f"{h}.png"
        if not f.exists():
            data = get(sk["url"].replace("http://", "https://"), {"User-Agent": "mc-stats-site/1.0"})
            if not data.startswith(b"\x89PNG"):
                raise ValueError("kein PNG")
            SKINS.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
            print(f"  neuer Skin für {j.get('name', uuid)}")
        return {"skin": h, "slim": (sk.get("metadata") or {}).get("model") == "slim"}
    except Exception as e:
        print(f"  Skin für {uuid[:8]} nicht lesbar ({e}) – behalte den alten")
        return prev


def vtz():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Europe/Vienna")
    except Exception:
        return timezone(timedelta(hours=1))


def hour_slots(t0, t1):
    """Zerlegt den Zeitraum t0..t1 in Stunden (Wiener Zeit): Liste von (Wochentag 0=Mo, Stunde, Minuten)."""
    out, t, tz = [], t0.astimezone(vtz()), vtz()
    end = t1.astimezone(tz)
    while t < end:
        nxt = min((t.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)), end)
        out.append((t.weekday(), t.hour, (nxt - t).total_seconds() / 60))
        t = nxt
    return out


def activity(out, players):
    """Spielzeit-Heatmap: verteilt die seit der letzten Aktualisierung dazugekommene Spielzeit auf die Stunden dazwischen.
    grid = Spieler-Minuten pro Wochentag/Stunde, cov = beobachtete Minuten pro Wochentag/Stunde (für den Durchschnitt)."""
    ap = out / "activity.json"
    a = jl(ap, {})
    now = datetime.now(timezone.utc)
    cur = {p["uuid"]: p.get("minutes", 0) for p in players}
    empty = lambda: [[0] * 24 for _ in range(7)]
    g, cov, per = a.get("grid") or empty(), a.get("cov") or empty(), a.get("players") or {}
    last = a.get("last") or {}
    try:
        t0 = datetime.fromisoformat(last["t"])
        span = (now - t0).total_seconds() / 60
    except Exception:
        span = 0
    if 0 < span <= 360:  # längere Lücken (Ausfall) nicht raten
        slots = hour_slots(t0, now)
        for wd, h, m in slots:
            cov[wd][h] = round(cov[wd][h] + m, 1)
        for u, mins in cur.items():
            d = min(mins - (last.get("m") or {}).get(u, mins), span)
            if d <= 0:
                continue
            pg = per.setdefault(u, empty())
            for wd, h, m in slots:
                share = d * m / span
                g[wd][h] = round(g[wd][h] + share, 1)
                pg[wd][h] = round(pg[wd][h] + share, 1)
    ap.write_text(json.dumps({"since": a.get("since") or now.astimezone(vtz()).date().isoformat(), "last": {"t": now.isoformat(), "m": cur},
                              "grid": g, "cov": cov, "players": per}, separators=(",", ":")))


LINES = [[r * 5 + c for c in range(5)] for r in range(5)] + [[r * 5 + c for r in range(5)] for c in range(5)] + [[i * 6 for i in range(5)], [4 + i * 4 for i in range(5)]]


def bingo(out, players, ov):
    """Wochen-Bingo: 5×5-Karte (Mitte frei), gezählt wird ab Montag 0:00. Wer zuerst eine Reihe/alle Felder hat, landet in 'winners'."""
    if (ov.get("bingo") or {}).get("enabled") is False:
        return None
    today = vienna_now().date()
    wk, start = week_id(today), today - timedelta(days=today.weekday())
    bp = out / "bingo.json"
    st = jl(bp, {})
    cur = {p["uuid"]: p.get("ch", {}) for p in players}
    names = {p["uuid"]: p["name"] for p in players}
    if st.get("week") != wk or not st.get("tasks"):
        rng = random.Random(wk + out.name)
        pick = rng.sample([t for t in CH.BINGO if t[0] in CH.BY_KEY], 24)
        tasks = [{"key": k, "target": n, "text": CH.bingo_text(k, n)} for k, n, _ in pick]
        tasks.insert(12, {"key": "free", "target": 0, "text": "Freies Feld"})
        st = {"week": wk, "start": start.isoformat(), "tasks": tasks, "base": cur, "winners": []}
        print(f"  Neue Bingo-Karte {wk}")
    new = {k: n for k, n, _ in CH.BINGO}
    for t in st["tasks"]:  # geänderte Zielwerte gelten sofort, auch für die laufende Woche
        if t["key"] in new:
            t["target"], t["text"] = new[t["key"]], CH.bingo_text(t["key"], new[t["key"]])
    base = st.setdefault("base", {})
    prog, now = {}, datetime.now(timezone.utc).isoformat(timespec="minutes")
    have = {(w["uuid"], w["type"]) for w in st["winners"]}
    for u in cur:
        base.setdefault(u, {})
        vals = [1 if t["key"] == "free" else round(max(cur[u].get(t["key"], 0) - base[u].get(t["key"], 0), 0), 1) for t in st["tasks"]]
        if any(vals[i] for i in range(25) if i != 12):
            prog[u] = vals
        done = [t["key"] == "free" or vals[i] >= t["target"] for i, t in enumerate(st["tasks"])]
        if any(all(done[i] for i in ln) for ln in LINES) and (u, "line") not in have:
            st["winners"].append({"uuid": u, "name": names[u], "type": "line", "t": now})
        if all(done) and (u, "full") not in have:
            st["winners"].append({"uuid": u, "name": names[u], "type": "full", "t": now})
    bp.write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")))
    return {"week": wk, "start": st["start"], "end": (start + timedelta(days=6)).isoformat(), "tasks": st["tasks"], "progress": prog, "winners": st["winners"]}


def streaks(out, players, ov):
    """Serien: Tage in Folge, an denen jemand mindestens 5 Minuten gespielt hat (Wiener Zeit)."""
    MIN = 5
    today = vienna_now().date()
    td, yd = today.isoformat(), (today - timedelta(days=1)).isoformat()
    sp = out / "streaks.json"
    st = jl(sp, None)
    cur = {p["uuid"]: p.get("minutes", 0) for p in players}
    if st is None:  # erster Lauf: Serien aus den gespeicherten Tagesdaten nachrechnen
        st = {"day": td, "base": dict(cur), "lastm": dict(cur), "p": {}, "seeded": {}}
        snaps = jl(out / "snapshots.json", {})
        days = sorted(snaps)
        active = {}
        for a, b in zip(days, days[1:]):
            if (date.fromisoformat(b) - date.fromisoformat(a)).days != 1:
                continue
            for u, v in snaps[b].items():
                if v.get("minutes", 0) - (snaps[a].get(u) or {}).get("minutes", v.get("minutes", 0)) >= MIN:
                    active.setdefault(u, set()).add(b)
        for u, ds in active.items():
            best = run = 0
            prev = None
            for d in sorted(ds):
                run = run + 1 if prev and (date.fromisoformat(d) - date.fromisoformat(prev)).days == 1 else 1
                best, prev = max(best, run), d
            st["p"][u] = {"cur": run, "best": best, "last": prev}
            if prev == td:  # heute schon gezählt
                st["base"][u] = cur.get(u, 0) - MIN
        print(f"  Serien aus {len(days)} Tagen nachgerechnet")
    if st.get("day") != td:
        st["day"], st["base"] = td, dict(st.get("lastm") or cur)
    seeds = (ov.get("streakSeed") or {}).get(out.name) or {}
    for u, sd in seeds.items():
        if sd and sd.get("stamp") and st.setdefault("seeded", {}).get(u) != sd["stamp"]:
            c = int(sd.get("cur") or 0)
            st["p"][u] = {"cur": c, "best": max(int(sd.get("best") or 0), c), "last": sd.get("last") or yd}
            st["seeded"][u] = sd["stamp"]
    for u, m in cur.items():
        b = st["base"].setdefault(u, 0 if u not in st.get("lastm", {}) else st["lastm"][u])
        q = st["p"].setdefault(u, {"cur": 0, "best": 0, "last": None})
        if m - b >= MIN and q.get("last") != td:
            q["cur"] = q["cur"] + 1 if q.get("last") == yd else 1
            q["last"], q["best"] = td, max(q.get("best", 0), q["cur"])
    st["lastm"] = cur
    sp.write_text(json.dumps(st, separators=(",", ":")))
    return {u: {"cur": q["cur"], "best": q["best"], "last": q["last"], "today": cur.get(u, 0) - st["base"].get(u, 0)}
            for u, q in st["p"].items() if u in cur}


def vienna_now():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Vienna"))
    except Exception:
        return datetime.now(timezone(timedelta(hours=1)))


def week_id(d):
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def challenge(out, players, ov):
    """Wochen-Challenge: zählt pro Spieler, wie viel seit Montag 0:00 (Wiener Zeit) dazugekommen ist."""
    cfg = ov.get("challenge") or {}
    if cfg.get("enabled") is False:
        return None
    today = vienna_now().date()
    wk, start = week_id(today), today - timedelta(days=today.weekday())
    cp = out / "challenge.json"
    st = jl(cp, {})
    cur = {p["uuid"]: p.get("ch", {}) for p in players}
    names = {p["uuid"]: p["name"] for p in players}
    forced = cfg.get("stat") if cfg.get("stat") in CH.BY_KEY and cfg.get("week") in (None, "", wk) else None
    hist = st.get("history") or []
    if st.get("week") != wk:
        if st.get("week") and st.get("stat") in CH.BY_KEY:
            hist = (hist + [{**CH.info(st["stat"]), "week": st["week"], "start": st.get("start"), "ranking": st.get("ranking") or []}])[-12:]
        recent = [h.get("stat") for h in hist[-4:]]
        if forced:
            stat = forced
        else:
            cand = sorted(k for k in CH.BY_KEY if k not in recent and sum(v.get(k, 0) for v in cur.values()) > 0) \
                or sorted(k for k in CH.BY_KEY if k not in recent)
            stat = random.Random(wk).choice(cand)
        st = {"week": wk, "start": start.isoformat(), "stat": stat, "base": cur, "history": hist}
        print(f"  Neue Wochen-Challenge {wk}: {CH.info(stat)['label']}")
    elif forced and forced != st.get("stat"):
        st["stat"] = forced
    stat, base = st["stat"], st.setdefault("base", {})
    dec = CH.info(stat)["dec"]
    for u in cur:
        base.setdefault(u, {})  # neuer Spieler: zählt ab 0
    vals = {u: round(cur[u].get(stat, 0) - base[u].get(stat, 0), dec) for u in cur}
    st["ranking"] = sorted(([u, names[u], v] for u, v in vals.items() if v > 0), key=lambda r: -r[2])
    cp.write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")))
    return {**CH.info(stat), "week": wk, "start": st["start"], "end": (start + timedelta(days=6)).isoformat(),
            "ranking": st["ranking"], "last": hist[-1] if hist else None}


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
        "mobs": {a[10:]: b for a, b in k.items() if b},
        "travel": travel, "top_mobs": top(k), "top_blocks": top(m), "top_used": top(u),
        "death_causes": top(kb, 5), "death_other": max(deaths - sum(kb.values()), 0),
        "f": {"eaten": sum(v for k_, v in u.items() if k_[10:] in FOOD), "fall_m": round(c.get("minecraft:fall_one_cm", 0) / 100),
              "trades": c.get("minecraft:traded_with_villager", 0), "fish": c.get("minecraft:fish_caught", 0),
              "bred": c.get("minecraft:animals_bred", 0), "sleeps": c.get("minecraft:sleep_in_bed", 0)},
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
    for p in players:
        p["ch"] = CH.compute(files[p["uuid"]])
    print(f"{sv['name']}: {len(players)} Spieler, Namen: {[p['name'] for p in players]}")
    out = D / "data" / sv["key"]
    out.mkdir(parents=True, exist_ok=True)
    prev = {p["uuid"]: {"skin": p.get("skin", ""), "slim": p.get("slim", False)} for p in jl(out / "stats.json", {}).get("players", [])}
    for p in players:
        p.update(prev.get(p["uuid"], {"skin": "", "slim": False}) if local else skin(p["uuid"], prev.get(p["uuid"], {"skin": "", "slim": False})))
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
    sp = out / "snapshots.json"
    snaps = json.loads(sp.read_text()) if sp.exists() else {}
    keys = ["minutes", "player_kills", "deaths", "km_travelled", "blocks_mined", "items_used", "entities_killed", "damage", "diamonds", "jumps"]
    snaps[today.isoformat()] = {p["uuid"]: {**{k: p.get(k, 0) for k in keys}, "x": p.get("x", {})} for p in players}
    for d in sorted(snaps)[:-35]:
        del snaps[d]
    sp.write_text(json.dumps(snaps, separators=(",", ":")))
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
    try:
        activity(out, players)
    except Exception as e:
        print("Heatmap nicht aktualisiert:", e)
    ov = jl(D / "overrides.json", {})
    extra = {}
    for name, fn in (("bingo", bingo), ("streaks", streaks)):
        try:
            extra[name] = fn(out, players, ov)
        except Exception as e:
            print(f"{name} nicht berechnet:", e)
            extra[name] = None
    try:
        chal = challenge(out, players, jl(D / "overrides.json", {}))
    except Exception as e:
        print("Wochen-Challenge nicht berechnet:", e)
        chal = None
    (out / "stats.json").write_text(json.dumps(
        {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "players": players, "status": status, "challenge": chal, **extra},
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
    # Liste der Challenge-Statistiken fürs Admin-Panel
    (D / "data" / "challenges.json").write_text(json.dumps([{"key": k, "label": l, "unit": u} for k, l, u, _, _ in CH.POOL], ensure_ascii=False))
    # alte Skins aufräumen, die kein Spieler mehr trägt
    SKINS.mkdir(parents=True, exist_ok=True)
    (SKINS / ".gitkeep").touch()
    used = {p.get("skin") for s in servers for p in jl(D / "data" / s["key"] / "stats.json", {}).get("players", [])}
    for f in SKINS.glob("*.png"):
        if f.stem not in used:
            f.unlink()
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
