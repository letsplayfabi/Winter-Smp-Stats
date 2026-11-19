"""Wochenrückblick als Bild (PNG) für Discord. Braucht Pillow (pip install pillow)."""
import io, json
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

D = Path("docs")
W, H = 1200, 675
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/", "/Library/Fonts/", "C:/Windows/Fonts/"]


def font(size, bold=True):
    names = ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "Arial.ttf", "arial.ttf"]
    for d in FONT_DIRS:
        for n in names:
            try:
                return ImageFont.truetype(d + n, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def hexc(s, default):
    s = str(s or default).lstrip("#")
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return hexc(default, "#ffffff")


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def num(v, dec=0):
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def face(p, size, fallback):
    f = D / "skins" / f"{p.get('skin') or '-'}.png"
    try:
        sk = Image.open(f).convert("RGBA")
        img = sk.crop((8, 8, 16, 16))
        img.alpha_composite(sk.crop((40, 8, 48, 16)))
        return img.resize((size, size), Image.NEAREST)
    except Exception:
        img = Image.new("RGBA", (size, size), fallback + (255,))
        d = ImageDraw.Draw(img)
        d.text((size / 2, size / 2), (p.get("name") or "?")[:1].upper(), font=font(size // 2), fill=(255, 255, 255), anchor="mm")
        return img


def fit(d, text, f, width):
    if d.textlength(text, font=f) <= width:
        return text
    while text and d.textlength(text + "…", font=f) > width:
        text = text[:-1]
    return text + "…"


def week_totals(key, players):
    """Was der ganze Server in den letzten 7 Tagen geschafft hat (aus den Tages-Schnappschüssen)."""
    try:
        snaps = json.loads((D / "data" / key / "snapshots.json").read_text())
    except Exception:
        snaps = {}
    lim = (date.today() - timedelta(days=7)).isoformat()
    old_days = [d for d in sorted(snaps) if d <= lim] or sorted(snaps)[:1]
    old = snaps[old_days[-1]] if old_days else {}
    tot = {"minutes": 0, "blocks_mined": 0, "deaths": 0, "km_travelled": 0}
    for p in players:
        o = old.get(p["uuid"], {k: 0 for k in tot})
        for k in tot:
            tot[k] += max((p.get(k) or 0) - (o.get(k) or 0), 0)
    return tot


def render(sv, players, theme, top, chal, climb):
    """players: Liste (Anzeigename, Spieler-Dict); top: [(Stunden, Name, Spieler)]; chal: (Bezeichnung, Name, Spieler, Wert-Text) oder None;
    climb: (Name, alter Platz, neuer Platz) oder None. Gibt PNG-Bytes zurück."""
    bg, pn = hexc(theme.get("bg"), "#0a111f"), hexc(theme.get("panel"), "#131b2b")
    fg, mu, ac = hexc(theme.get("text"), "#ffffff"), hexc(theme.get("muted"), "#8fa0b8"), hexc(theme.get("accent"), "#52e585")
    pc = [hexc(c, "#52e585") for c in (theme.get("players") or ["#52e585", "#45b0f5", "#e9bc57"])][:3]
    while len(pc) < 3:
        pc.append(ac)
    img = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(img)
    # dezenter Farbverlauf oben
    for y in range(220):
        d.line([(0, y), (W, y)], fill=mix(bg, ac, 0.16 * (1 - y / 220)) + (255,))
    end, start = date.today() - timedelta(days=1), date.today() - timedelta(days=7)
    d.text((48, 40), "WOCHENRÜCKBLICK", font=font(22), fill=ac)
    d.text((48, 70), fit(d, sv["name"], font(54), 700), font=font(54), fill=fg)
    d.text((W - 48, 52), f"{start:%d.%m.} – {end:%d.%m.%Y}", font=font(24, False), fill=mu, anchor="ra")

    # Podest: meiste Spielzeit
    d.rounded_rectangle((40, 160, 640, 520), 22, fill=pn)
    d.text((70, 184), "Meiste Spielzeit", font=font(26), fill=fg)
    slots = [(0, 340, 118), (1, 140, 88), (2, 540, 62)]  # (Platz-Index, Mitte x, Podesthöhe) – Platz 1 in der Mitte
    for i, cx, hgt in slots:
        if i >= len(top):
            continue
        h, name, p = top[i]
        top_y = 500 - hgt
        d.rounded_rectangle((cx - 85, top_y, cx + 85, 500), 14, fill=mix(pn, pc[i], 0.6))
        d.text((cx, top_y + hgt / 2), str(i + 1), font=font(44), fill=fg, anchor="mm")
        d.text((cx, top_y - 12), num(h, 1) + " h", font=font(24), fill=pc[i], anchor="ms")
        d.text((cx, top_y - 44), fit(d, name, font(22), 180), font=font(22), fill=fg, anchor="ms")
        hs = 84 if i == 0 else 72
        img.alpha_composite(face(p, hs, pc[i]), (cx - hs // 2, top_y - 74 - hs))
    if not top:
        d.text((340, 340), "Diese Woche war niemand online.", font=font(22, False), fill=mu, anchor="mm")

    # Server gesamt
    t = week_totals(sv["key"], [p for _, p in players])
    tiles = [("Gespielt", num(t["minutes"] / 60, 1) + " h"), ("Blöcke abgebaut", num(t["blocks_mined"])),
             ("Tode", num(t["deaths"])), ("Gereist", num(t["km_travelled"], 1) + " km")]
    d.text((680, 166), "Der ganze Server diese Woche", font=font(22), fill=mu)
    for k, (label, val) in enumerate(tiles):
        x, y = 680 + (k % 2) * 245, 206 + (k // 2) * 157
        d.rounded_rectangle((x, y, x + 230, y + 140), 18, fill=pn)
        d.text((x + 22, y + 24), label, font=font(20, False), fill=mu)
        d.text((x + 22, y + 62), fit(d, val, font(38), 190), font=font(38), fill=fg)

    # Fußzeile: Challenge + Aufsteiger
    d.rounded_rectangle((40, 545, W - 40, 640), 22, fill=pn)
    x = 70
    if chal:
        label, name, p, val = chal
        img.alpha_composite(face(p, 56, ac), (x, 565))
        d.text((x + 72, 566), "Wochen-Challenge: " + fit(d, label, font(19, False), 330), font=font(19, False), fill=mu)
        d.text((x + 72, 594), fit(d, f"{name} gewinnt mit {val}", font(24), 420), font=font(24), fill=fg)
        x = 640
    if climb:
        d.text((x, 566), "Aufsteiger der Woche", font=font(19, False), fill=mu)
        d.text((x, 594), fit(d, f"{climb[0]}: Platz {climb[1]} → {climb[2]}", font(24), W - 80 - x), font=font(24), fill=fg)
    if not chal and not climb:
        d.text((W // 2, 592), "Neue Woche, neues Glück – bis nächsten Montag!", font=font(22, False), fill=mu, anchor="mm")
    out = io.BytesIO()
    img.convert("RGB").save(out, "PNG", optimize=True)
    return out.getvalue()
