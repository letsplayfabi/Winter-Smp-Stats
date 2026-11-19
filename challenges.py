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
