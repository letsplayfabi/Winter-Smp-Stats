# Projekt: Minecraft-Statistikseite (Winter SMP + Chill SMP)

Sprache: Antworte immer auf Deutsch. Der Besitzer ist kein Profi-Entwickler – erkläre Schritte kurz und verständlich.

## Überblick
- Zwei Minecraft-Server, beide auf exaroton gehostet, beide mit Fabric:
  - **Winter SMP** – Minecraft 26.3, Fabric Loader 0.19.5 (Key `winter`, Secret `EXAROTON_SERVER_ID`)
  - **Chill SMP** – Minecraft 1.21.10 (Key `chill`, Secret `EXAROTON_SERVER_ID_2`; Stats liegen in `chillsmp/stats`)
- Statische Website auf GitHub Pages in diesem Repo (`Winter-Smp-Stats`), Ordner `docs/`.
- Keine Datenbank, kein Server: alles läuft über GitHub Actions + JSON-Dateien.

## Dateien
- `fetch_stats.py` – holt Stats-Dateien über die exaroton-API, schreibt `docs/data/<server>/stats.json` + History.
- `notify.py` – Discord-Meldungen per Webhook (neue Events, Wochen-Top-3 montags, Meilensteine, Erfolge, Ziele). Muss robust sein: darf nie abstürzen, weil ein Event-Feld fehlt oder komisch formatiert ist.
- `challenges.py` – Liste aller Statistiken für die Wochen-Challenge (gemeinsam genutzt von fetch_stats.py und notify.py).
- `recap.py` – zeichnet den Wochenrückblick als PNG (Pillow) für Discord.
- `servers.json` – Serverliste, pro Server `extra`-Kategorien und `hide`.
- `docs/index.html` – die Seite (Server-Reiter oben, Bestenliste, Spielerprofile mit Skin/Kopf, Events-Tab, Platzänderungen ▲▼ zur Vorwoche, Besucher-Einstellungen wie „mich markieren“ und mehrere Statistiken pro Zeile).
- `docs/admin.html` – Admin-Panel (Reiter neben den Server-Reitern): Farben (auch pro Spieler), Kategorienamen, Kategorien pro Server per Haken, Spieler, Events anlegen/bearbeiten (Bild, Name, Beschreibung, Datum, Uhrzeit), eigene Statistiken wie „Bezahlt“, Server-Ziele, Erfolge, Discord-Einstellungen.
- `docs/overrides.json` – vom Admin bearbeitbare Inhalte (u. a. `challenge`, `showGallery`, `notify.recap`).
- `docs/gallery.json` + `docs/gallery/` – Galerie-Bilder (im Admin hochladbar, Reiter „Galerie“ auf der Seite).
- `docs/skins/<hash>.png` – Skins, holt `fetch_stats.py` direkt von Mojang; die Seite zeichnet Kopf und Körper selbst daraus. Alte Skins werden automatisch gelöscht.
- `docs/data/<server>/activity.json` – Spielzeit-Heatmap: `grid` = Spieler-Minuten, `cov` = beobachtete Minuten je Wochentag/Stunde (Wiener Zeit), `players` = dasselbe pro Spieler. Wird aus der Spielzeit-Differenz zwischen zwei Läufen berechnet; Lücken über 6 h werden ausgelassen.
- `overrides.json` → `people` (Steckbriefe, global pro UUID: name, role, fav, since, bday „MM-TT“, about) und `places` (Orte für die Karte: name, type, server, dim, x, y, z, owner, gallery = ID eines Bildes aus gallery.json, desc).
- `docs/data/<server>/challenge.json` – Stand der Wochen-Challenge (Startwerte ab Montag 0:00 Wiener Zeit, Verlauf der letzten 12 Wochen).
- `docs/manifest.webmanifest`, `docs/sw.js`, Icons – Seite als App auf dem Handy-Startbildschirm.
- `.github/workflows/update-stats.yml` – alle 30 Minuten + manuell; `notify.py` läuft mit `continue-on-error: true`, damit Discord-Fehler das Speichern nie blockieren.
- `.github/workflows/discord-test.yml` – Testnachricht an Discord.
- `mod/bundle.txt` + `.github/workflows/build-mod.yml` – LiveStats-Mod (siehe unten).

## LiveStats-Mod
- Alle Quelldateien stecken in `mod/bundle.txt` (Abschnitte `=== FILE: pfad ===`). Der Workflow „Mod bauen“ packt sie aus und baut zwei Varianten:
  - `yarn` → Minecraft 1.21.10, Java 21 → für **Chill SMP**
  - `mojang` → Minecraft 26.3, Java 25 → für **Winter SMP**
- Änderungen an der Mod immer in `mod/bundle.txt` machen, nicht in einem ausgepackten Ordner.
- Die Mod meldet Join/Leave/Tod/Erfolge/Diamanten/Start/Stop live an Discord und kann optional per GitHub-Token den Workflow `update-stats.yml` anstoßen.
- Konfiguration auf dem Server: `config/livestats.json` (serverName, discordWebhook, githubToken, githubRepo …).
- Braucht die Fabric API auf dem Server.

## Wichtige Regeln
- **Niemals** Tokens, Webhooks oder Passwörter ins Repo schreiben – das Repo ist öffentlich. Secrets gehören in GitHub Secrets (`EXAROTON_TOKEN`, `EXAROTON_SERVER_ID`, `EXAROTON_SERVER_ID_2`, `DISCORD_WEBHOOK`) bzw. in die Config auf exaroton.
- Vor dem Pushen: `git pull --rebase`, weil der Stats-Bot regelmäßig selbst committet.
- Neue Funktionen sollen im Admin-Panel bearbeitbar sein, nicht nur im Code.
- Workflows bei Bedarf mit `gh workflow run …` starten und mit `gh run watch` beobachten.

## Bingo, Serien, Bestiarium, Prognosen, Stats-Raten
- `docs/data/<server>/bingo.json` – Wochen-Bingo (5×5, Mitte frei, Aufgaben aus `challenges.BINGO`, Startwerte ab Montag, `winners` für Reihe/volle Karte).
- `docs/data/<server>/streaks.json` – Serien (Tage in Folge mit ≥ 5 min Spielzeit, Wiener Zeit). Erster Lauf rechnet aus `snapshots.json` nach. Vorgaben aus dem Admin: `overrides.streakSeed[server][uuid] = {cur, best, last, stamp}` – wird einmal pro `stamp` übernommen.
- `stats.json` enthält zusätzlich `bingo`, `streaks` und pro Spieler `mobs` (alle besiegten Mobs) fürs Bestiarium (Reiter `#bestiary`).
- Prognosen (Server-Ziele und Profil) rechnet die Seite aus `snapshots.json` (Tempo der letzten 7 Tage).
- Minispiel „Stats-Raten“: Funktion `gStatsGuess`, Spiel-Schlüssel `statsguess` (`guess`/`gGuess` gehört dem Schätzspiel!).
- Discord: Bingo-Gewinner und Serien-Meilensteine (7, 14, 21, 30, 50 … Tage).

## Adventskalender, Wichteln, Spielstil, Befehle im Spiel
- `advent.py` – Geschenke (FINAL = Türchen 24, NIKOLAUS = fest an Türchen 6, GUT + NORMAL = Rest) und TASKS (eine Aufgabe pro Türchen). Die Mod setzt beim ersten `/advent` pro Türchen einen Startwert aus den Live-Stats (world/stats bzw. world/players/stats) und gibt das Geschenk, sobald die Aufgabe geschafft ist. Nachgeholt: Ziel × 2^(Tage Verspätung), max. MAX_FAKTOR. Raketen bekommen eine Stern-Explosion. Jeder Spieler bekommt dieselben 24 Geschenke in anderer Reihenfolge (Zufall pro Jahr+UUID). `fetch_stats.py` schreibt `docs/data/advent.json`.
- Mod: Befehle `/bingo`, `/challenge`, `/serie`, `/advent`, `/seite`. Die Mod lädt alle 2 Minuten `stats.json` und `advent.json` von der Seite (`siteUrl`, `serverKey` in livestats.json, sonst automatisch). `/advent` gibt Items mit Namen und Beschreibung (Compat.give / Compat.item – neue Item-IDs dort ergänzen, in BEIDEN Compat-Varianten). Abgeholte Türchen: `config/livestats-advent.json`.
- Wichteln: geheim, bis der Admin mit dem Auflösungs-Schlüssel „Auflösen“ klickt (`revealed` in wichteln.json). Admin lost aus (nur Spieler ab X Stunden), speichert `docs/wichteln.json` verschlüsselt (SHA-256-Hash des Codes + AES-GCM mit PBKDF2-Schlüssel). Codes werden NICHT gespeichert.
- Spielstil + „Wer spielt wie du?“: nur im Browser (Profil), Werte pro Spielstunde, normiert auf den Server.
- Reiter „🎄 Advent“: `overrides.advent` = auto (Dezember) | always | off.

## Minispiele, globale Rekorde, Umfragen, Dashboard
- Neue Spiele: `redstone` (gRedstone), `snake` (gSnake), `craftle` (gCraftle, tägliches Rezept aus CR, Ergebnis in localStorage „craftle:Datum“), `whobuilt` (gWhoBuilt, nutzt Galerie-Feld „by“).
- Globale Rekorde: Spiel-Ende zeigt Code (recCode: 6 Bit Spiel-Index aus REC_GAMES, 12 Bit Tag seit 1.1.2026, 30 Bit Punkte, 12 Bit Prüfsumme, Base32). Spieler tippt `/rekord CODE`, die Mod prüft Prüfsumme + max. 2 Tage Alter und speichert in `config/livestats-moddata.json`. REC_GAMES-Reihenfolge NIE ändern (in index.html, fetch_stats.py und Mod REC_NAMES gleich).
- Umfragen: `overrides.polls` [{id,q,opts,end}], abgestimmt mit `/vote N` (neueste aktive Umfrage).
- Die Mod schickt Rekorde/Stimmen bei jedem Workflow-Start als Eingabe `moddata` mit → `fetch_stats.save_moddata` → `docs/data/<server>/moddata.json`. Beste Rekorde landen als `rec` in jedem Spieler (stats.json) → Erfolge mit Metrik `rec_<spiel>` (nur Spiele, bei denen mehr besser ist).
- „Mein Dashboard“ (dashBox) erscheint oben für den markierten Spieler (`PREF.me`).

## Nur im Browser (index.html)
- Spielerkarte: Knopf „📸 Als Bild teilen“ im Profil zeichnet ein 1080×1350-PNG per Canvas (Teilen über navigator.share oder Herunterladen).
- Saison-Deko: `overrides.deco` = auto | winter | halloween | newyear | off; Besucher können sie in den Einstellungen abschalten; bei „weniger Bewegung“ im System automatisch aus.

## Wochen-Challenge
- Jede Woche eine Statistik aus `challenges.py`; zufällig (keine Wiederholung der letzten 4 Wochen) oder im Admin fest gewählt.
- Montags meldet `notify.py` den Gewinner und schickt den Wochenrückblick als Bild. Vorschau: Workflow „Discord-Test“.

## Offene Ideen
- Mod bauen, auf beiden Servern installieren und konfigurieren.
- Eigene Domain für die Seite (optional).
