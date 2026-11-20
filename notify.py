#!/usr/bin/env python3
"""Discord-Meldungen: neue Events, Wochen-Top-3 (montags), Meilensteine. Braucht das GitHub-Secret DISCORD_WEBHOOK."""
import json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

D = Path("docs")
STATE = D / "data" / "notify_state.json"
HOOK = os.environ.get("DISCORD_WEBHOOK", "").strip()
MS = {"hours": ("Stunden gespielt", [10, 25, 50, 100, 250, 500, 1000]),
      "diamonds": ("💎 Diamanten", [25, 50, 100, 250, 500, 1000]),
      "blocks_mined": ("Blöcke abgebaut", [10000, 25000, 50000, 100000, 250000, 500000]),
      "entities_killed": ("Entities getötet", [500, 1000, 5000, 10000])}


def jl(p, default):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


def mval(p, m):
    x = p.get("x") or {}
    return {"playtime": p.get("minutes", 0), "player_kills": p.get("player_kills", 0), "deaths": p.get("deaths", 0),
            "travel": p.get("km_travelled", 0), "mined": p.get("blocks_mined", 0), "used": p.get("items_used", 0),
            "killed": p.get("entities_killed", 0), "damage": p.get("damage", 0), "diamonds": p.get("diamonds", 0),
            "jumps": p.get("jumps", 0), "netherite": x.get("debris", 0), "creepers": x.get("creepers", 0),
            "netherrack": x.get("netherrack", 0), "deepslate": x.get("deepslate", 0), "elytra": x.get("aviate_km", 0)}.get(m)


BASE = ["playtime", "player_kills", "deaths", "travel", "mined", "used", "killed", "damage", "diamonds"]
HI = {k: 1 for k in BASE + ["netherite", "creepers", "netherrack", "deepslate", "elytra"]}
HI["deaths"] = 0


def places(recs, keys):
    pts = {u: 0.0 for u in recs}
    for key in keys:
        vals = {u: mval(r, key) or 0 for u, r in recs.items()}
        order = sorted(vals, key=lambda u: -vals[u] if HI[key] else vals[u])
        i = 0
        while i < len(order):
            j = i
            while j < len(order) and vals[order[j]] == vals[order[i]]:
                j += 1
            s = sum(len(order) - x for x in range(i, j))
            for x in range(i, j):
                pts[order[x]] += s / (j - i)
            i = j
    return {u: 1 + sum(1 for v in pts.values() if v > pts[u]) for u in pts}


def climber(sv, players, ov, today):
    """Größter Aufsteiger in der Gesamtwertung seit ~7 Tagen: (Name, alter Platz, neuer Platz) oder None."""
    snaps = jl(D / "data" / sv["key"] / "snapshots.json", {})
    days = sorted(d for d in snaps if d < today)
    if not days:
        return None
    lim = (datetime.fromisoformat(today) - timedelta(days=7)).date().isoformat()
    cand = [d for d in days if d <= lim]
    old = snaps[cand[-1] if cand else days[0]]
    en = (((ov.get("servers") or {}).get(sv["key"]) or {}).get("enabled")) or [k for k in BASE + sv.get("extra", []) if k not in sv.get("hide", [])]
    keys = [k for k in en if k in HI]
    now = {p["uuid"]: p for _, p in players if p["uuid"] in old}
    if len(now) < 2 or not keys:
        return None
    names = {p["uuid"]: n for n, p in players}
    a, b = places({u: old[u] for u in now}, keys), places(now, keys)
    u, gain = max(((u, a[u] - b[u]) for u in now), key=lambda t: t[1])
    return (names[u], a[u], b[u]) if gain > 0 else None


def fmt_date(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(s or ""))
    return f"{m[3]}.{m[2]}.{m[1]}" if m else str(s or "")


def post(payload):
    payload["allowed_mentions"] = {"parse": []}
    req = urllib.request.Request(HOOK, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "mc-stats-site/1.0"})
    urllib.request.urlopen(req, timeout=20).read()


def post_png(payload, filename, png):
    """Discord-Nachricht mit Bild-Anhang (multipart)."""
    payload["allowed_mentions"] = {"parse": []}
    payload["attachments"] = [{"id": 0, "filename": filename}]
    b = "----mcstats" + os.urandom(8).hex()
    body = (f'--{b}\r\nContent-Disposition: form-data; name="payload_json"\r\nContent-Type: application/json\r\n\r\n'.encode()
            + json.dumps(payload).encode()
            + f'\r\n--{b}\r\nContent-Disposition: form-data; name="files[0]"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode()
            + png + f"\r\n--{b}--\r\n".encode())
    req = urllib.request.Request(HOOK, body, {"Content-Type": f"multipart/form-data; boundary={b}", "User-Agent": "mc-stats-site/1.0"})
    urllib.request.urlopen(req, timeout=30).read()


def pname_ov(ov, key, p):
    o = (((ov.get("servers") or {}).get(key) or {}).get("players") or {}).get(p["uuid"], {})
    return None if o.get("hidden") else (o.get("display_name") or p["name"])


def fmtv(v, unit="", dec=0):
    t = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return t + (" " + unit if unit and unit != "×" else "×" if unit == "×" else "")


def weekly_post(sv, ov, site, today, chal_seen=None, preview=False):
    """Wochen-Top-3 + Wochen-Challenge + Rückblick-Bild. Gibt (Embed, PNG oder None) zurück, oder (None, None)."""
    d = jl(D / "data" / sv["key"] / "stats.json", {})
    players = [(pname_ov(ov, sv["key"], p), p) for p in d.get("players", [])]
    players = [(n, p) for n, p in players if n]
    byid = {p["uuid"]: (n, p) for n, p in players}
    top = sorted([(p.get("week_hours", 0), n, p) for n, p in players if p.get("week_hours", 0) > 0], key=lambda t: -t[0])[:3]
    medals = ["🥇", "🥈", "🥉"]
    desc = "\n".join(f"{medals[i]} **{n}** – {fmtv(h, 'h', 1)}" for i, (h, n, _) in enumerate(top))
    c = climber(sv, players, ov, today)
    if c:
        desc += f"\n\n📈 **Aufsteiger der Woche:** **{c[0]}** (Platz {c[1]} → {c[2]})"
    chal, ch = d.get("challenge") or {}, None
    last = chal.get("last") or {}
    if last.get("week") and (preview or (chal_seen is not None and chal_seen.get(sv["key"]) != last["week"])):
        if chal_seen is not None:
            chal_seen[sv["key"]] = last["week"]
        rk = [(byid[u][0], byid[u][1], v) for u, _n, v in last.get("ranking") or [] if u in byid][:3]
        if rk:
            desc += f"\n\n🎯 **Wochen-Challenge: {last['label']}**\n" + "\n".join(
                f"{medals[i]} **{n}** – {fmtv(v, last.get('unit', ''), last.get('dec', 0))}" for i, (n, _p, v) in enumerate(rk))
            ch = (last["label"], rk[0][0], rk[0][1], fmtv(rk[0][2], last.get("unit", ""), last.get("dec", 0)))
    if chal.get("label"):
        desc += f"\n\n🎲 **Neue Challenge diese Woche:** {chal['label']} – [zur Rangliste]({site}#{sv['key']})"
    if not top and not ch:
        return None, None
    emb = {"title": f"🏆 Wochenrückblick – {sv['name']}" + (" (Vorschau)" if preview else ""), "url": site, "color": 0x52E585, "description": desc.strip()}
    png = None
    if (ov.get("notify") or {}).get("recap", True):
        try:
            import recap
            png = recap.render(sv, players, ov.get("theme") or {}, top, ch, c)
        except Exception as e:
            print("Rückblick-Bild nicht erstellt:", e)
    return emb, png


def main():
    if "--test" in sys.argv:
        if not HOOK:
            print("FEHLER: Das Secret DISCORD_WEBHOOK fehlt oder ist leer.")
            sys.exit(1)
        owner, _, repo = os.environ.get("GITHUB_REPOSITORY", "/").partition("/")
        try:
            post({"embeds": [{"title": "✅ Testnachricht", "color": 0x52E585,
                              "url": os.environ.get("SITE_URL") or f"https://{owner.lower()}.github.io/{repo}/",
                              "description": "Dein Server-Leaderboard ist mit Discord verbunden. Neue Events, Wochen-Top-3 und Meilensteine landen ab jetzt hier."}]})
            print("Testnachricht gesendet.")
            ov = jl(D / "overrides.json", {})
            site = os.environ.get("SITE_URL") or f"https://{owner.lower()}.github.io/{repo}/"
            for sv in jl(D / "servers.json", []):
                emb, png = weekly_post(sv, ov, site, datetime.now(timezone.utc).date().isoformat(), preview=True)
                if emb and png:
                    emb["image"] = {"url": f"attachment://rueckblick-{sv['key']}.png"}
                    post_png({"embeds": [emb]}, f"rueckblick-{sv['key']}.png", png)
                elif emb:
                    post({"embeds": [emb]})
                print("Vorschau Wochenrückblick gesendet:", sv["name"])
        except Exception as e:
            print("FEHLER beim Senden:", e)
            sys.exit(1)
        return
    if not HOOK:
        print("Kein DISCORD_WEBHOOK gesetzt – keine Discord-Meldungen.")
        return
    ov = jl(D / "overrides.json", {})
    cfg = {"events": True, "weekly": True, "milestones": True, "achievements": True, "goals": True, "birthdays": True, **(ov.get("notify") or {})}
    servers = jl(D / "servers.json", [])
    events = (jl(D / "events.json", {}) or {}).get("events", [])
    first = not STATE.exists()
    st = jl(STATE, {})
    st.setdefault("events", [])
    ach_first = "ach" not in st
    st.setdefault("ms", {})
    st.setdefault("ach", {})
    owner, _, repo = os.environ.get("GITHUB_REPOSITORY", "/").partition("/")
    site = os.environ.get("SITE_URL") or f"https://{owner.lower()}.github.io/{repo}/"
    now = datetime.now(timezone.utc)
    embeds, lines, files = [], [], []

    def pname(key, p):
        o = (((ov.get("servers") or {}).get(key) or {}).get("players") or {}).get(p["uuid"], {})
        return None if o.get("hidden") else (o.get("display_name") or p["name"])

    # 1) neue Events
    for e in events:
        eid = e.get("id")
        if not eid or eid in st["events"]:
            continue
        st["events"].append(eid)
        if first or not cfg["events"]:
            continue
        try:
            wann = (fmt_date(e.get("date")) + (" " + str(e["time"]) + " Uhr" if e.get("time") else "")).strip() or "–"
            emb = {"title": f"📅 Neues Event: {e.get('name') or 'Event'}", "url": site + "#events", "color": 0x5865F2,
                   "description": (e.get("desc") or "")[:500], "fields": [{"name": "Wann", "value": wann}]}
            sv = next((s["name"] for s in servers if s["key"] == e.get("server")), None)
            if sv:
                emb["fields"].append({"name": "Server", "value": sv})
            if e.get("image"):
                emb["image"] = {"url": site + e["image"]}
            embeds.append(emb)
        except Exception as ex:
            print("Event konnte nicht gemeldet werden:", eid, ex)

    # Geburtstage (ab 8 Uhr Wiener Zeit, einmal pro Jahr und Person)
    try:
        from zoneinfo import ZoneInfo
        vnow = now.astimezone(ZoneInfo("Europe/Vienna"))
    except Exception:
        vnow = now + timedelta(hours=1)
    md, leap = vnow.strftime("%m-%d"), vnow.year % 4 == 0 and (vnow.year % 100 != 0 or vnow.year % 400 == 0)
    bd = st.setdefault("bday", {})
    for u, pp in (ov.get("people") or {}).items():
        b = (pp or {}).get("bday") or ""
        if not (b == md or (b == "02-29" and md == "02-28" and not leap)) or bd.get(u) == vnow.date().isoformat() or vnow.hour < 8:
            continue
        bd[u] = vnow.date().isoformat()
        if not first and cfg["birthdays"]:
            lines.append(f"🎂 Heute hat **{pp.get('name') or 'jemand'}** Geburtstag – alles Gute! 🎉")

    # 2) Meilensteine + 3) Wochen-Top-3
    today = now.date().isoformat()
    weekly = cfg["weekly"] and now.weekday() == 0 and now.hour >= 8 and st.get("weekly") != today
    for sv in servers:
        d = jl(D / "data" / sv["key"] / "stats.json", {})
        players = [(pname(sv["key"], p), p) for p in d.get("players", [])]
        players = [(n, p) for n, p in players if n]
        seen = st["ms"].setdefault(sv["key"], {})
        for n, p in players:
            for metric, (label, ths) in MS.items():
                best = max([t for t in ths if p.get(metric, 0) >= t], default=0)
                prev = seen.setdefault(p["uuid"], {}).get(metric, 0)
                if best > prev:
                    seen[p["uuid"]][metric] = best
                    if not first and cfg["milestones"]:
                        lines.append(f"🎉 **{n}** ({sv['name']}): {best:,} {label}!".replace(",", "."))
        names = {p["uuid"]: n for n, p in players}
        sa = st["ach"].setdefault(sv["key"], {})
        for a in ov.get("achievements") or []:
            if a.get("server") not in (None, "all", sv["key"]) or not players:
                continue
            vals = {p["uuid"]: mval(p, a.get("metric")) for _, p in players}
            if any(v is None for v in vals.values()):
                continue
            if a.get("type") == "top":
                best = (min if a.get("dir") == "min" else max)(vals.values())
                holders = [] if a.get("dir") != "min" and best <= 0 else [u for u, v in vals.items() if v == best]
            else:
                holders = [u for u, v in vals.items() if v >= (a.get("value") or 0)]
            prev = sa.get(a["id"], [])
            new = [u for u in holders if u not in prev]
            sa[a["id"]] = holders
            if new and not ach_first and cfg["achievements"] and a.get("announce", True):
                title = f"{a.get('icon') or '🏆'} **{a['title']}**"
                who = ", ".join(f"**{names[u]}**" for u in new)
                if a.get("type") == "top" and prev:
                    lines.append(f"👑 {title} ({sv['name']}) geht jetzt an {who} (vorher {', '.join(names.get(u, 'jemand') for u in prev)})")
                else:
                    lines.append(f"🏆 {who} hat den Erfolg {title} erhalten ({sv['name']})")
        if weekly:
            emb, png = weekly_post(sv, ov, site, today, st.setdefault("chal", {}))
            if emb and png:
                emb["image"] = {"url": f"attachment://rueckblick-{sv['key']}.png"}
                files.append(({"embeds": [emb]}, f"rueckblick-{sv['key']}.png", png))
            elif emb:
                embeds.append(emb)
    goals = st.setdefault("goals", {})
    for g in ov.get("goals") or []:
        m = g.get("metric", "")
        if m.startswith("c_"):
            c = next((c for c in (ov.get("custom") or []) if "c_" + str(c.get("id")) == m), None)
            tot = sum(float(v or 0) for v in (c or {}).get("values", {}).values())
        else:
            tot = 0
            for s2 in servers:
                if g.get("server") not in (None, "all", s2["key"]):
                    continue
                for p in jl(D / "data" / s2["key"] / "stats.json", {}).get("players", []):
                    if pname(s2["key"], p):
                        tot += mval(p, m) or 0
        target = float(g.get("target") or 0)
        reached = target > 0 and tot >= target
        prev = goals.get(g.get("id"))
        if prev is None:
            goals[g["id"]] = "done" if reached else "open"
        elif prev == "open" and reached:
            goals[g["id"]] = "done"
            if cfg["goals"] and g.get("announce", True):
                show = (lambda v, m=m: (f"{v / 60:,.0f} h" if m == "playtime" else f"{v:,.0f}").replace(",", "."))
                embeds.append({"title": "🎯 Server-Ziel erreicht!", "url": site, "color": 0xE9BC57,
                               "description": f"**{g.get('name', 'Ziel')}**\n{show(tot)} / {show(target)} – das hat die ganze Community gemeinsam geschafft! 🎉"})
        elif prev == "done" and not reached:
            goals[g["id"]] = "open"
    if first or weekly:
        st["weekly"] = today

    lines = list(dict.fromkeys(lines))  # identische Zeilen nur einmal
    posts = [{"embeds": embeds[i:i + 10]} for i in range(0, len(embeds), 10)]
    chunk = ""
    for ln in lines:
        if len(chunk) + len(ln) > 1800:
            posts.append({"content": chunk})
            chunk = ""
        chunk += ln + "\n"
    if chunk:
        posts.append({"content": chunk})
    try:
        for p in posts:
            post(p)
        for payload, name, png in files:
            post_png(payload, name, png)
    except Exception as e:
        print("Discord-Meldung fehlgeschlagen:", e)
        return  # Stand nicht speichern, nächster Lauf versucht es erneut
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st))
    print(f"Discord: {len(posts)} Nachricht(en) gesendet" + (" (erster Lauf: nur Ausgangsstand gespeichert)" if first else ""))


if __name__ == "__main__":
    main()
