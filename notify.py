#!/usr/bin/env python3
"""Discord-Meldungen: neue Events, Wochen-Top-3 (montags), Meilensteine. Braucht das GitHub-Secret DISCORD_WEBHOOK."""
import json, os, urllib.request
from datetime import datetime, timezone
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


def post(payload):
    payload["allowed_mentions"] = {"parse": []}
    req = urllib.request.Request(HOOK, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "mc-stats-site/1.0"})
    urllib.request.urlopen(req, timeout=20).read()


def main():
    if not HOOK:
        print("Kein DISCORD_WEBHOOK gesetzt – keine Discord-Meldungen.")
        return
    ov = jl(D / "overrides.json", {})
    cfg = {"events": True, "weekly": True, "milestones": True, **(ov.get("notify") or {})}
    servers = jl(D / "servers.json", [])
    events = (jl(D / "events.json", {}) or {}).get("events", [])
    first = not STATE.exists()
    st = jl(STATE, {})
    st.setdefault("events", [])
    st.setdefault("ms", {})
    owner, _, repo = os.environ.get("GITHUB_REPOSITORY", "/").partition("/")
    site = os.environ.get("SITE_URL") or f"https://{owner.lower()}.github.io/{repo}/"
    now = datetime.now(timezone.utc)
    embeds, lines = [], []

    def pname(key, p):
        o = (((ov.get("servers") or {}).get(key) or {}).get("players") or {}).get(p["uuid"], {})
        return None if o.get("hidden") else (o.get("display_name") or p["name"])

    # 1) neue Events
    for e in events:
        if e["id"] in st["events"]:
            continue
        st["events"].append(e["id"])
        if first or not cfg["events"]:
            continue
        when = e["date"].split("-")
        emb = {"title": f"📅 Neues Event: {e['name']}", "url": site + "#events", "color": 0x5865F2,
               "description": (e.get("desc") or "")[:500],
               "fields": [{"name": "Wann", "value": f"{when[2]}.{when[1]}.{when[0]} {e.get('time') or ''}".strip() + (" Uhr" if e.get("time") else "")}]}
        sv = next((s["name"] for s in servers if s["key"] == e.get("server")), None)
        if sv:
            emb["fields"].append({"name": "Server", "value": sv})
        if e.get("image"):
            emb["image"] = {"url": site + e["image"]}
        embeds.append(emb)

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
        if weekly:
            top = sorted([(p.get("week_hours", 0), n) for n, p in players if p.get("week_hours", 0) > 0], reverse=True)[:3]
            if top:
                medals = ["🥇", "🥈", "🥉"]
                embeds.append({"title": f"🏆 Top 3 der Woche – {sv['name']}", "url": site, "color": 0x52E585,
                               "description": "\n".join(f"{medals[i]} **{n}** – {h:.1f} h".replace(".", ",") for i, (h, n) in enumerate(top))})
    if first or weekly:
        st["weekly"] = today

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
    except Exception as e:
        print("Discord-Meldung fehlgeschlagen:", e)
        return  # Stand nicht speichern, nächster Lauf versucht es erneut
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st))
    print(f"Discord: {len(posts)} Nachricht(en) gesendet" + (" (erster Lauf: nur Ausgangsstand gespeichert)" if first else ""))


if __name__ == "__main__":
    main()
