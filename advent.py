"""Adventskalender: Belohnungen und Zuteilung.

Jeder Spieler bekommt GENAU dieselben 24 Geschenke – nur in einer anderen, zufälligen Reihenfolge.
- Türchen 6 (Nikolaus): immer das Nikolaus-Netherit
- Türchen 24: für alle der Weihnachtsapfel
- Jedes Türchen hat eine einfache Aufgabe (TASKS). Wer ein Türchen später nachholt, muss pro Tag Verspätung
  doppelt so viel schaffen (höchstens MAX_FAKTOR-mal so viel).
Zum Ändern einfach die Listen anpassen (Item-ID, Anzahl, Name, Beschreibung, deutscher Item-Name).
Erlaubte Item-IDs stehen in der Mod (Compat.item) – neue Items bitte dort ergänzen.
"""
import random

# (ID, Minecraft-Item, Anzahl, Name, Beschreibung, deutscher Item-Name)
FINAL = ("weihnachtsapfel", "minecraft:enchanted_golden_apple", 1, "✦ Weihnachtsapfel {year} ✦", "Frohe Weihnachten vom ganzen Server!", "Verzauberter Goldener Apfel")

NIKOLAUS = ("nikolaus_netherit", "minecraft:netherite_ingot", 1, "Nikolaus-Netherit", "Vom Nikolaus persönlich geschmiedet.", "Netheritbarren")

GUT = [
    ("wintersterne", "minecraft:diamond", 2, "Funkelnde Wintersterne", "Zwei Sterne, frisch vom Himmel gefallen.", "Diamant"),
    ("christbaumkugeln", "minecraft:golden_apple", 2, "Goldene Christbaumkugeln", "Zu schade zum Aufhängen.", "Goldener Apfel"),
]

NORMAL = [
    ("adventsdiamant", "minecraft:diamond", 1, "❄ Adventsdiamant", "Kalt, klar und funkelnd.", "Diamant"),
    ("eiskristall", "minecraft:diamond", 1, "❄ Eiskristall", "Schmilzt garantiert nicht.", "Diamant"),
    ("weihnachtsgeld", "minecraft:emerald", 5, "Weihnachtsgeld", "Für den nächsten Dorfbesuch.", "Smaragd"),
    ("schlittenkufen", "minecraft:iron_ingot", 16, "Schlittenkufen", "Damit der Schlitten gut gleitet.", "Eisenbarren"),
    ("lametta", "minecraft:gold_ingot", 8, "Lametta", "Glänzt fast wie echt.", "Goldbarren"),
    ("adventskuchen", "minecraft:cake", 1, "Adventskuchen", "Mit extra viel Zuckerguss.", "Kuchen"),
    ("vanillekipferl", "minecraft:cookie", 16, "Vanillekipferl", "Nach Omas Rezept.", "Keks"),
    ("rudolphs_snack", "minecraft:golden_carrot", 8, "Rudolphs Lieblingssnack", "Gib Rudolph nicht alle.", "Goldene Karotte"),
    ("weihnachtsmagie", "minecraft:experience_bottle", 8, "Weihnachtsmagie", "Vorsichtig öffnen.", "Erfahrungsfläschchen"),
    ("nordlicht", "minecraft:lapis_lazuli", 16, "Nordlicht", "Ein Stück Polarnacht.", "Lapislazuli"),
    ("geschenkanhaenger", "minecraft:name_tag", 1, "Geschenkanhänger", "Für dein liebstes Haustier.", "Namensschild"),
    ("rentiersattel", "minecraft:saddle", 1, "Rentiersattel", "Passt (leider) nur auf Pferde.", "Sattel"),
    ("silvesterrakete", "minecraft:firework_rocket", 16, "Silvesterrakete", "Bitte erst zu Silvester zünden!", "Feuerwerksrakete"),
    ("schneeballschlacht", "minecraft:snowball", 16, "Schneeballschlacht", "Zielen, werfen, lachen.", "Schneeball"),
    ("adventslichter", "minecraft:lantern", 4, "Adventslichter", "Für eine gemütliche Basis.", "Laterne"),
    ("lebkuchen", "minecraft:pumpkin_pie", 4, "Lebkuchen", "Na gut – fast Lebkuchen.", "Kürbiskuchen"),
    ("maerchenbuecher", "minecraft:bookshelf", 2, "Märchenbücher", "Für lange Winterabende.", "Bücherregal"),
    ("gluehwein", "minecraft:honey_bottle", 4, "Glühwein (alkoholfrei)", "Wärmt von innen.", "Honigflasche"),
    ("weihnachtsglocke", "minecraft:bell", 1, "Weihnachtsglocke", "Kling, Glöckchen, klingelingeling.", "Glocke"),
    ("christbaum", "minecraft:spruce_sapling", 8, "Christbaum zum Selberziehen", "Gießen nicht vergessen.", "Fichtensetzling"),
]


MAX_FAKTOR = 64  # nachgeholte Türchen werden höchstens 64-mal so schwer

CROPS = ["wheat", "carrots", "potatoes", "beetroots", "sugar_cane", "melon", "pumpkin", "nether_wart", "cocoa", "sweet_berry_bush", "bamboo", "cactus"]
FOOD = ["cookie", "bread", "baked_potato", "cooked_beef", "cooked_porkchop", "cooked_chicken", "cooked_mutton", "cooked_cod", "cooked_salmon",
        "apple", "carrot", "golden_carrot", "pumpkin_pie", "mushroom_stew", "beetroot_soup", "rabbit_stew", "sweet_berries", "melon_slice"]


def m(*ids, suffix=()):  # abgebaute Blöcke
    return {"t": "mined", "ids": list(ids), "suffix": list(suffix)}


def k(*ids):  # besiegte Mobs
    return {"t": "killed", "ids": list(ids)}


def c(*ids):  # allgemeine Statistiken
    return {"t": "custom", "ids": list(ids)}


# Aufgabe pro Türchen: (Text mit {n}, Ziel, [Teile], Teiler)
TASKS = [
    ("{n} Baumstämme abbauen", 10, [m(suffix=("_log", "_stem", "_wood", "_hyphae"))], 1),
    ("{n} Fische angeln", 3, [c("fish_caught")], 1),
    ("{n} Kohleerze abbauen", 10, [m("coal_ore", "deepslate_coal_ore")], 1),
    ("{n} Pflanzen ernten", 16, [m(*CROPS)], 1),
    ("{n} Zombies besiegen", 3, [k("zombie", "husk", "drowned", "zombie_villager")], 1),
    ("{n} km zu Fuß gehen", 1, [c("walk_one_cm")], 100000),
    ("{n} Eisenerze abbauen", 5, [m("iron_ore", "deepslate_iron_ore")], 1),
    ("{n} Schneebälle werfen", 16, [{"t": "used", "ids": ["snowball"]}], 1),
    ("{n} Skelette besiegen", 3, [k("skeleton", "stray", "bogged")], 1),
    ("{n} Tiere züchten", 3, [c("animals_bred")], 1),
    ("{n} Stein abbauen", 64, [m("stone")], 1),
    ("{n} Fackeln herstellen", 16, [{"t": "crafted", "ids": ["torch"]}], 1),
    ("{n}× springen", 100, [c("jump")], 1),
    ("{n} Spinnen besiegen", 2, [k("spider", "cave_spider")], 1),
    ("{n}× etwas Leckeres essen", 5, [{"t": "used", "ids": FOOD}], 1),
    ("{n} Sand oder Kies abbauen", 32, [m("sand", "red_sand", "gravel")], 1),
    ("{n} Creeper besiegen", 1, [k("creeper")], 1),
    ("{n} Blätter abbauen", 32, [m(suffix=("_leaves",))], 1),
    ("{n}× mit einem Dorfbewohner handeln", 1, [c("traded_with_villager")], 1),
    ("{n} Tiefenschiefer abbauen", 32, [m("deepslate")], 1),
    ("{n} Brote backen", 3, [{"t": "crafted", "ids": ["bread"]}], 1),
    ("{n} Erde oder Gras abbauen", 64, [m("dirt", "grass_block", "coarse_dirt", "rooted_dirt")], 1),
    ("{n} Mobs besiegen", 10, [c("mob_kills")], 1),
    ("{n}× im Bett schlafen", 1, [c("sleep_in_bed")], 1),
]


def build(uuids, year):
    """Gibt {rewards, tasks, players} zurück. players[uuid] = Liste mit 24 Belohnungs-IDs (Türchen 1–24)."""
    rewards = {}
    for tier, items in (("final", [FINAL]), ("gut", [NIKOLAUS] + GUT), ("normal", NORMAL)):
        for rid, item, count, name, lore, de in items:
            rewards[rid] = {"item": item, "count": count, "name": name.replace("{year}", str(year)), "lore": lore, "de": de, "tier": tier,
                            "firework": item == "minecraft:firework_rocket"}
    assert len(GUT) + len(NORMAL) == 22, "GUT + NORMAL müssen zusammen 22 Geschenke sein (Türchen 1–23 ohne den 6.)"
    assert len(TASKS) == 24, "Es braucht genau 24 Aufgaben"
    tasks = [{"text": t, "target": n, "parts": parts, "div": div} for t, n, parts, div in TASKS]
    players = {}
    for u in sorted(set(uuids)):
        rng = random.Random(f"{year}:{u}")
        rest = [g[0] for g in GUT] + [n[0] for n in NORMAL]
        rng.shuffle(rest)
        players[u] = rest[:5] + [NIKOLAUS[0]] + rest[5:] + [FINAL[0]]  # Türchen 6 = Nikolaus-Netherit, 24 = Weihnachtsapfel
    return {"year": year, "rewards": rewards, "tasks": tasks, "maxFactor": MAX_FAKTOR, "players": players}
