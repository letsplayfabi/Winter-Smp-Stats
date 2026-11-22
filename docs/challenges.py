"""Pool der Statistiken für die Wochen-Challenge (wird von fetch_stats.py und notify.py benutzt)."""

LOGS = ("_log", "_stem", "_wood", "_hyphae")
CROPS = {"wheat", "carrots", "potatoes", "beetroots", "sugar_cane", "melon", "pumpkin", "nether_wart", "cocoa", "sweet_berry_bush", "bamboo", "cactus"}
ZOMBIES = {"zombie", "zombie_villager", "husk", "drowned"}
SKELETONS = {"skeleton", "stray", "bogged", "wither_skeleton"}
SPIDERS = {"spider", "cave_spider"}
FARM = {"cow", "pig", "sheep", "chicken", "rabbit", "mooshroom", "goat"}
FOOD = {"apple", "baked_potato", "beetroot", "beetroot_soup", "bread", "carrot", "chorus_fruit", "cooked_beef", "cooked_chicken", "cooked_cod",
        "cooked_mutton", "cooked_porkchop", "cooked_rabbit", "cooked_salmon", "cookie", "dried_kelp", "enchanted_golden_apple", "glow_berries",
        "golden_apple", "golden_carrot", "honey_bottle", "melon_slice", "mushroom_stew", "poisonous_potato", "potato", "pufferfish", "pumpkin_pie",
        "rabbit_stew", "beef", "chicken", "cod", "mutton", "porkchop", "rabbit", "salmon", "rotten_flesh", "spider_eye", "suspicious_stew",
        "sweet_berries", "tropical_fish"}


def _sum(d, keep):
    return sum(v for k, v in d.items() if keep(k[10:] if k.startswith("minecraft:") else k))


def _c(key, div=1):
    return lambda s: s["c"].get("minecraft:" + key, 0) / div


# (Schlüssel, Bezeichnung, Einheit, Nachkommastellen, Funktion)
POOL = [
    ("fish", "Fische geangelt", "", 0, _c("fish_caught")),
    ("bred", "Tiere gezüchtet", "", 0, _c("animals_bred")),
    ("trades", "Handel mit Dorfbewohnern", "", 0, _c("traded_with_villager")),
    ("villager_talk", "Mit Dorfbewohnern geredet", "×", 0, _c("talked_to_villager")),
    ("sleeps", "Im Bett geschlafen", "×", 0, _c("sleep_in_bed")),
    ("jumps", "Sprünge", "", 0, _c("jump")),
    ("deaths", "Tode (wer stirbt am meisten?)", "", 0, _c("deaths")),
    ("mobs", "Mobs getötet", "", 0, _c("mob_kills")),
    ("dmg_dealt", "Schaden ausgeteilt", "HP", 0, _c("damage_dealt", 10)),
    ("dmg_taken", "Schaden eingesteckt", "HP", 0, _c("damage_taken", 10)),
    ("walk", "Zu Fuß gelaufen", "km", 1, _c("walk_one_cm", 100000)),
    ("sprint", "Gesprintet", "km", 1, _c("sprint_one_cm", 100000)),
    ("swim", "Geschwommen", "km", 1, _c("swim_one_cm", 100000)),
    ("boat", "Boot gefahren", "km", 1, _c("boat_one_cm", 100000)),
    ("horse", "Geritten", "km", 1, _c("horse_one_cm", 100000)),
    ("elytra", "Mit der Elytra geflogen", "km", 1, _c("aviate_one_cm", 100000)),
    ("minecart", "Lore gefahren", "km", 1, _c("minecart_one_cm", 100000)),
    ("crouch", "Geschlichen", "m", 0, _c("crouch_one_cm", 100)),
    ("climb", "Geklettert", "m", 0, _c("climb_one_cm", 100)),
    ("fall", "Tief gefallen", "m", 0, _c("fall_one_cm", 100)),
    ("cake", "Kuchenstücke gegessen", "", 0, _c("eat_cake_slice")),
    ("chests", "Truhen geöffnet", "×", 0, _c("open_chest")),
    ("enchant", "Gegenstände verzaubert", "", 0, _c("enchant_item")),
    ("drops", "Items fallen gelassen", "", 0, _c("drop")),
    ("crafting_table", "Werkbank benutzt", "×", 0, _c("interact_with_crafting_table")),
    ("furnace", "Ofen benutzt", "×", 0, _c("interact_with_furnace")),
    ("bell", "Glocke geläutet", "×", 0, _c("bell_ring")),
    ("flowers_potted", "Blumen eingetopft", "", 0, _c("pot_flower")),
    ("noteblock", "Notenblock gespielt", "×", 0, _c("play_noteblock")),
    ("mined", "Blöcke abgebaut", "", 0, lambda s: sum(s["m"].values())),
    ("logs", "Baumstämme gefällt", "", 0, lambda s: _sum(s["m"], lambda k: k.endswith(LOGS))),
    ("ores", "Erze abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k.endswith("_ore") or k == "ancient_debris")),
    ("diamonds", "Diamanterz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("diamond_ore", "deepslate_diamond_ore"))),
    ("coal", "Kohleerz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("coal_ore", "deepslate_coal_ore"))),
    ("iron", "Eisenerz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("iron_ore", "deepslate_iron_ore"))),
    ("stone", "Stein abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k == "stone")),
    ("deepslate", "Tiefenschiefer abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k == "deepslate")),
    ("netherrack", "Netherrack abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k == "netherrack")),
    ("dirt", "Erde und Gras abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("dirt", "grass_block", "coarse_dirt", "rooted_dirt"))),
    ("sand", "Sand und Kies abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("sand", "red_sand", "gravel"))),
    ("crops", "Pflanzen geerntet", "", 0, lambda s: _sum(s["m"], lambda k: k in CROPS)),
    ("leaves", "Blätter abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k.endswith("_leaves"))),
    ("zombies", "Zombies besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in ZOMBIES)),
    ("skeletons", "Skelette besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in SKELETONS)),
    ("creepers", "Creeper besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k == "creeper")),
    ("spiders", "Spinnen besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in SPIDERS)),
    ("endermen", "Endermen besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k == "enderman")),
    ("farm_animals", "Nutztiere geschlachtet", "", 0, lambda s: _sum(s["k"], lambda k: k in FARM)),
    ("crafted", "Gegenstände hergestellt", "", 0, lambda s: sum(s["cr"].values())),
    ("torches", "Fackeln hergestellt", "", 0, lambda s: _sum(s["cr"], lambda k: k == "torch")),
    ("food", "Essen gegessen", "", 0, lambda s: _sum(s["u"], lambda k: k in FOOD)),
    ("pearls", "Enderperlen geworfen", "", 0, lambda s: _sum(s["u"], lambda k: k == "ender_pearl")),
    ("rockets", "Feuerwerksraketen gezündet", "", 0, lambda s: _sum(s["u"], lambda k: k == "firework_rocket")),
    ("bonemeal", "Knochenmehl benutzt", "", 0, lambda s: _sum(s["u"], lambda k: k == "bone_meal")),
    ("picked", "Items aufgesammelt", "", 0, lambda s: sum(s["p"].values())),
    ("broken", "Werkzeuge kaputt gemacht", "", 0, lambda s: sum(s["b"].values())),
    ("blazes", "Lohen besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in ("blaze",))),
    ("ghasts", "Ghasts besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in ("ghast",))),
    ("witches", "Hexen besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in ("witch",))),
    ("phantoms", "Phantome besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in ("phantom",))),
    ("slimes", "Schleime besiegt", "", 0, lambda s: _sum(s["k"], lambda k: k in ("slime",))),
    ("debris", "Antiken Schrott abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("ancient_debris",))),
    ("emerald", "Smaragderz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("emerald_ore", "deepslate_emerald_ore",))),
    ("lapis", "Lapislazulierz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("lapis_ore", "deepslate_lapis_ore",))),
    ("redstone", "Redstoneerz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("redstone_ore", "deepslate_redstone_ore",))),
    ("gold", "Golderz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("gold_ore", "deepslate_gold_ore", "nether_gold_ore",))),
    ("copper", "Kupfererz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("copper_ore", "deepslate_copper_ore",))),
    ("quartz", "Netherquarzerz abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("nether_quartz_ore",))),
    ("obsidian", "Obsidian abgebaut", "", 0, lambda s: _sum(s["m"], lambda k: k in ("obsidian",))),
    ("snowballs", "Schneebälle geworfen", "", 0, lambda s: _sum(s["u"], lambda k: k in ("snowball",))),
    ("eggs", "Eier geworfen", "", 0, lambda s: _sum(s["u"], lambda k: k in ("egg",))),
    ("arrows", "Pfeile mit dem Bogen geschossen", "", 0, lambda s: _sum(s["u"], lambda k: k in ("bow",))),
    ("fishing_casts", "Angel ausgeworfen", "×", 0, lambda s: _sum(s["u"], lambda k: k in ("fishing_rod",))),
    ("bread", "Brote gebacken", "", 0, lambda s: _sum(s["cr"], lambda k: k in ("bread",))),
    ("cookies", "Kekse gebacken", "", 0, lambda s: _sum(s["cr"], lambda k: k in ("cookie",))),
    ("enderchest", "Endertruhe geöffnet", "×", 0, _c("open_enderchest")),
    ("barrel", "Fass geöffnet", "×", 0, _c("open_barrel")),
    ("anvil", "Amboss benutzt", "×", 0, _c("interact_with_anvil")),
    ("pig", "Auf einem Schwein geritten", "km", 1, _c("pig_one_cm", 100000)),
    ("shield", "Schaden mit dem Schild geblockt", "HP", 0, _c("damage_blocked_by_shield", 10)),
    ("records", "Schallplatten abgespielt", "", 0, _c("play_record")),
    ("raids", "Überfälle gewonnen", "", 0, _c("raid_win")),
]
BY_KEY = {k: (label, unit, dec, fn) for k, label, unit, dec, fn in POOL}


def compute(raw):
    """Alle Challenge-Werte eines Spielers aus seiner Stats-Datei."""
    st = raw.get("stats", {})
    s = {"c": st.get("minecraft:custom", {}), "m": st.get("minecraft:mined", {}), "k": st.get("minecraft:killed", {}),
         "u": st.get("minecraft:used", {}), "cr": st.get("minecraft:crafted", {}), "p": st.get("minecraft:picked_up", {}),
         "b": st.get("minecraft:broken", {})}
    out = {}
    for k, _label, _unit, dec, fn in POOL:
        try:
            v = round(fn(s), dec) if dec else int(fn(s))
        except Exception:
            v = 0
        if v:
            out[k] = v
    return out


def info(key):
    label, unit, dec, _ = BY_KEY.get(key, (key, "", 0, None))
    return {"stat": key, "label": label, "unit": unit, "dec": dec}


# Bingo-Aufgaben: (Schlüssel aus POOL, Ziel pro Woche, Text mit {n})
BINGO = [
    ("fish", 100, "{n} Fische angeln"), ("bred", 500, "{n} Tiere züchten"), ("trades", 50, "{n}× mit Dorfbewohnern handeln"),
    ("villager_talk", 100, "{n}× mit Dorfbewohnern reden"), ("sleeps", 30, "{n}× im Bett schlafen"), ("jumps", 5000, "{n}× springen"),
    ("mobs", 500, "{n} Mobs besiegen"), ("walk", 5, "{n} km laufen"), ("swim", 0.5, "{n} km schwimmen"), ("boat", 10, "{n} km Boot fahren"),
    ("horse", 100, "{n} km reiten"), ("minecart", 25, "{n} km Lore fahren"),
    ("crouch", 100, "{n} m schleichen"), ("climb", 50, "{n} m klettern"), ("fall", 2000, "{n} m tief fallen"), ("cake", 7, "{n} Kuchenstücke essen"),
    ("chests", 500, "{n}× eine Truhe öffnen"), ("enchant", 3, "{n} Gegenstände verzaubern"), ("crafting_table", 20, "{n}× die Werkbank benutzen"),
    ("furnace", 10, "{n}× den Ofen benutzen"), ("bell", 10, "{n}× eine Glocke läuten"), ("flowers_potted", 1, "{n} Blume eintopfen"),
    ("noteblock", 10, "{n}× einen Notenblock spielen"), ("logs", 256, "{n} Baumstämme fällen"), ("ores", 150, "{n} Erze abbauen"),
    ("diamonds", 15, "{n} Diamanterze abbauen"), ("coal", 64, "{n} Kohleerze abbauen"), ("iron", 64, "{n} Eisenerze abbauen"),
    ("netherrack", 2000, "{n} Netherrack abbauen"), ("sand", 320, "{n} Sand oder Kies abbauen"), ("crops", 512, "{n} Pflanzen ernten"),
    ("leaves", 100, "{n} Blätter abbauen"), ("zombies", 50, "{n} Zombies besiegen"), ("skeletons", 50, "{n} Skelette besiegen"),
    ("creepers", 10, "{n} Creeper besiegen"), ("spiders", 20, "{n} Spinnen besiegen"), ("endermen", 5, "{n} Endermen besiegen"),
    ("farm_animals", 10, "{n} Nutztiere schlachten"), ("torches", 32, "{n} Fackeln herstellen"), ("food", 200, "{n}× etwas essen"),
    ("pearls", 3, "{n} Enderperlen werfen"), ("bonemeal", 10, "{n}× Knochenmehl benutzen"),
    ("broken", 1, "{n} Werkzeug kaputt machen"), ("dmg_taken", 1000, "{n} HP Schaden einstecken"),
    ("picked", 5000, "{n} Items aufsammeln"), ("drops", 2000, "{n} Items fallen lassen"), ("crafted", 100, "{n} Gegenstände herstellen"),
    ("stone", 1000, "{n} Stein abbauen"), ("deepslate", 800, "{n} Tiefenschiefer abbauen"), ("dirt", 500, "{n} Erde oder Gras abbauen"),
    ("blazes", 20, "{n} Lohen besiegen"), ("ghasts", 3, "{n} Ghasts besiegen"), ("witches", 3, "{n} Hexen besiegen"),
    ("phantoms", 10, "{n} Phantome besiegen"), ("slimes", 10, "{n} Schleime besiegen"), ("debris", 4, "{n} Antiken Schrott abbauen"),
    ("emerald", 3, "{n} Smaragderze abbauen"), ("lapis", 20, "{n} Lapislazulierze abbauen"), ("redstone", 30, "{n} Redstoneerze abbauen"),
    ("gold", 20, "{n} Golderze abbauen"), ("copper", 50, "{n} Kupfererze abbauen"), ("quartz", 64, "{n} Netherquarzerze abbauen"),
    ("obsidian", 10, "{n} Obsidian abbauen"), ("snowballs", 64, "{n} Schneebälle werfen"), ("eggs", 16, "{n} Eier werfen"),
    ("arrows", 50, "{n} Pfeile mit dem Bogen schießen"), ("fishing_casts", 100, "{n}× die Angel auswerfen"), ("bread", 32, "{n} Brote backen"),
    ("cookies", 64, "{n} Kekse backen"), ("enderchest", 20, "{n}× in eine Endertruhe schauen"), ("barrel", 20, "{n}× ein Fass öffnen"),
    ("anvil", 5, "{n}× den Amboss benutzen"), ("pig", 1, "{n} km auf einem Schwein reiten"), ("shield", 1000, "{n} HP Schaden mit dem Schild blocken"),
    ("records", 3, "{n}× eine Schallplatte abspielen"), ("raids", 5, "{n} Überfälle gewinnen"),
]


def bingo_text(key, target):
    for k, t, text in BINGO:
        if k == key:
            return text.replace("{n}", f"{target:g}".replace(".", ","))
    return key
