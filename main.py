import json
import os
import random
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import discord
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN environment variable is not set!")


# ==============================
# Data definitions
# ==============================


@dataclass(frozen=True)
class Animal:
    animal_id: str
    emoji: str
    rarity: str
    rarity_index: int
    role: str
    hp: int
    atk: int
    defense: int
    aliases: List[str]


@dataclass(frozen=True)
class Food:
    food_id: str
    emoji: str
    rarity: str
    cost: int
    hp_bonus: int
    atk_bonus: int
    def_bonus: int
    ability: str
    aliases: List[str]


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE_PATH = os.path.join(BASE_DIR, "users.json")


RARITY_ORDER = [
    ("COMMON", "⚪"),
    ("UNCOMMON", "🟢"),
    ("RARE", "🔵"),
    ("EPIC", "🟣"),
    ("LEGENDARY", "🟡"),
    ("SPECIAL", "🌈"),
    ("HIDDEN", "⚫"),
]

RARITY_INDEX = {name: idx for idx, (name, _symbol) in enumerate(RARITY_ORDER)}

ROLE_EMOJI = {
    "TANK": "🛡️",
    "ATTACK": "⚔️",
    "SUPPORT": "🧪",
}


# Mutation tiers attached to owned animal instances.
# Schema (per animal_id):
# {
#   "none": 2,
#   "golden": 1,
#   "diamond": 0,
#   "emerald": 0,
#   "rainbow": 0,
# }
MUTATIONS = ["none", "golden", "diamond", "emerald", "rainbow"]
MUTATION_ALIASES = {
    "none": {"none", "normal", "base"},
    "golden": {"golden", "gold", "g"},
    "diamond": {"diamond", "dia", "d"},
    "emerald": {"emerald", "emer", "em"},
    "rainbow": {"rainbow", "rb", "rain"},
}
MUTATION_META = {
    "none": {"emoji": "", "multiplier": 1.0, "ability_multiplier": 1.0},
    "golden": {
        "emoji": "<a:9922yellowfire:1392567259687551037>",
        "multiplier": 1.0,
        "ability_multiplier": 1.25,
    },
    "diamond": {
        "emoji": "<a:3751bluefire:1392567237453545524>",
        "multiplier": 1.0,
        "ability_multiplier": 1.5,
    },
    "emerald": {
        "emoji": "<a:9922greenfire:1392567257821089994>",
        "multiplier": 1.0,
        "ability_multiplier": 2.0,
    },
    "rainbow": {
        "emoji": "<a:8308rainbowfire:1392567255170158780>",
        "multiplier": 1.0,
        "ability_multiplier": 5.0,
    },
}


def normalize_mutation_key(value: str) -> str:
    key = value.strip().lower()
    for canonical, aliases in MUTATION_ALIASES.items():
        if key == canonical or key in aliases:
            return canonical
    if key not in MUTATIONS:
        raise ValueError(f"Unknown mutation key: {value}")
    return key


def default_mutation_counts() -> Dict[str, int]:
    return {mutation: 0 for mutation in MUTATIONS}


def roll_mutation() -> str:
    roll = random.random() * 100
    if roll < 1.0:
        return "rainbow"
    if roll < 1.0 + 2.5:
        return "emerald"
    if roll < 1.0 + 2.5 + 5.0:
        return "diamond"
    if roll < 1.0 + 2.5 + 5.0 + 10.0:
        return "golden"
    return "none"


def format_mutation_label(mutation: str) -> str:
    mutation_key = normalize_mutation_key(mutation)
    emoji = MUTATION_META[mutation_key]["emoji"]
    return f"{mutation_key.capitalize()} {emoji}".strip()


def get_owned_count(profile: Dict, animal_id: str, mutation: str) -> int:
    mutation = normalize_mutation_key(mutation)
    zoo_entry = profile.get("zoo", {}).get(animal_id, {})
    if isinstance(zoo_entry, dict):
        return max(0, int(zoo_entry.get(mutation, 0)))
    return max(0, int(zoo_entry if zoo_entry else 0)) if mutation == "none" else 0


def total_owned_species(profile: Dict, animal_id: str) -> int:
    zoo_entry = profile.get("zoo", {}).get(animal_id, {})
    if isinstance(zoo_entry, dict):
        return sum(max(0, int(qty)) for qty in zoo_entry.values())
    return max(0, int(zoo_entry if zoo_entry else 0))


def add_animal(profile: Dict, animal_id: str, mutation: str, qty: int) -> None:
    mutation = normalize_mutation_key(mutation)
    qty = max(0, int(qty))
    if qty <= 0:
        return
    zoo = profile.setdefault("zoo", {})
    current = zoo.get(animal_id, {})
    if not isinstance(current, dict):
        current = {"none": max(0, int(current))}
    bucket = default_mutation_counts()
    for key, value in current.items():
        try:
            normalized_key = normalize_mutation_key(key)
        except ValueError:
            continue
        bucket[normalized_key] = max(0, int(value))
    bucket[mutation] = bucket.get(mutation, 0) + qty
    zoo[animal_id] = bucket


def remove_animal(profile: Dict, animal_id: str, mutation: str, qty: int) -> int:
    mutation = normalize_mutation_key(mutation)
    qty = max(0, int(qty))
    if qty <= 0:
        return 0
    zoo = profile.setdefault("zoo", {})
    current = zoo.get(animal_id, {})
    if not isinstance(current, dict):
        current = {"none": max(0, int(current))}
    bucket = default_mutation_counts()
    for key, value in current.items():
        try:
            normalized_key = normalize_mutation_key(key)
        except ValueError:
            continue
        bucket[normalized_key] = max(0, int(value))
    owned = bucket.get(mutation, 0)
    removed = min(owned, qty)
    bucket[mutation] = max(0, owned - removed)
    zoo[animal_id] = bucket
    return removed


def build_animals() -> Dict[str, Animal]:
    animals: List[Animal] = []

    def add(
        rarity: str,
        rarity_index: int,
        role: str,
        animal_id: str,
        emoji: str,
        hp: int,
        atk: int,
        defense: int,
        aliases: List[str],
    ):
        animals.append(
            Animal(
                animal_id=animal_id,
                emoji=emoji,
                rarity=rarity,
                rarity_index=rarity_index,
                role=role,
                hp=hp,
                atk=atk,
                defense=defense,
                aliases=aliases,
            )
        )

    rarity_map = {name: idx for idx, (name, _) in enumerate(RARITY_ORDER)}

    # COMMON
    add("COMMON", rarity_map["COMMON"], "ATTACK", "mouse", "🐁", 7, 6, 1, ["mouse", "m"])
    add("COMMON", rarity_map["COMMON"], "ATTACK", "chicken", "🐔", 7, 5, 1, ["chicken", "chick"])
    add("COMMON", rarity_map["COMMON"], "ATTACK", "fish", "🐟", 7, 5, 1, ["fish"])
    add("COMMON", rarity_map["COMMON"], "TANK", "pig", "🐖", 10, 3, 3, ["pig"])
    add("COMMON", rarity_map["COMMON"], "TANK", "cow", "🐄", 11, 3, 3, ["cow"])
    add("COMMON", rarity_map["COMMON"], "TANK", "ram", "🐏", 9, 4, 3, ["ram"])
    add("COMMON", rarity_map["COMMON"], "TANK", "sheep", "🐑", 9, 3, 4, ["sheep"])
    add("COMMON", rarity_map["COMMON"], "TANK", "goat", "🐐", 8, 4, 3, ["goat"])
    add("COMMON", rarity_map["COMMON"], "SUPPORT", "bug", "🐛", 7, 3, 3, ["bug"])
    add("COMMON", rarity_map["COMMON"], "SUPPORT", "ant", "🐜", 6, 3, 3, ["ant"])
    add("COMMON", rarity_map["COMMON"], "SUPPORT", "bird", "🐦", 7, 3, 3, ["bird"])

    # UNCOMMON
    add("UNCOMMON", rarity_map["UNCOMMON"], "ATTACK", "dog", "🐕", 8, 7, 2, ["dog"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "ATTACK", "cat", "🐈", 8, 7, 2, ["cat"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "ATTACK", "snake", "🐍", 8, 8, 2, ["snake"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "TANK", "horse", "🐎", 13, 4, 4, ["horse"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "TANK", "boar", "🐗", 12, 5, 4, ["boar"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "TANK", "deer", "🦌", 12, 4, 5, ["deer"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "TANK", "turtle", "🐢", 14, 2, 5, ["turtle"])
    add("UNCOMMON", rarity_map["UNCOMMON"], "SUPPORT", "tropicalfish", "🐠", 8, 4, 4, ["tropicalfish", "tfish"])

    # RARE
    add("RARE", rarity_map["RARE"], "ATTACK", "wolf", "🐺", 9, 9, 3, ["wolf"])
    add("RARE", rarity_map["RARE"], "ATTACK", "fox", "🦊", 9, 9, 3, ["fox"])
    add("RARE", rarity_map["RARE"], "ATTACK", "dolphin", "🐬", 10, 8, 3, ["dolphin"])
    add("RARE", rarity_map["RARE"], "TANK", "crocodile", "🐊", 15, 5, 6, ["crocodile", "croc"])
    add("RARE", rarity_map["RARE"], "SUPPORT", "raccoon", "🦝", 9, 4, 5, ["raccoon"])
    add("RARE", rarity_map["RARE"], "SUPPORT", "owl", "🦉", 9, 3, 6, ["owl"])
    add("RARE", rarity_map["RARE"], "SUPPORT", "parrot", "🦜", 8, 4, 5, ["parrot"])

    # EPIC
    add("EPIC", rarity_map["EPIC"], "TANK", "elephant", "🐘", 18, 4, 8, ["elephant", "ele"])
    add("EPIC", rarity_map["EPIC"], "TANK", "hippo", "🦛", 19, 4, 8, ["hippo"])
    add("EPIC", rarity_map["EPIC"], "TANK", "llama", "🦙", 16, 5, 7, ["llama"])
    add("EPIC", rarity_map["EPIC"], "TANK", "giraffe", "🦒", 17, 5, 7, ["giraffe"])
    add("EPIC", rarity_map["EPIC"], "SUPPORT", "swan_epic", "🦢", 11, 4, 7, ["swan"])
    add("EPIC", rarity_map["EPIC"], "SUPPORT", "flamingo", "🦩", 10, 5, 6, ["flamingo"])

    # LEGENDARY
    add("LEGENDARY", rarity_map["LEGENDARY"], "ATTACK", "shark", "🦈", 14, 11, 4, ["shark"])
    add("LEGENDARY", rarity_map["LEGENDARY"], "TANK", "mammoth", "🦣", 22, 5, 9, ["mammoth"])
    add("LEGENDARY", rarity_map["LEGENDARY"], "TANK", "seal", "🦭", 20, 6, 8, ["seal"])
    add("LEGENDARY", rarity_map["LEGENDARY"], "TANK", "whale", "🐳", 24, 4, 10, ["whale"])

    # SPECIAL
    add("SPECIAL", rarity_map["SPECIAL"], "SUPPORT", "octopus", "🐙", 12, 5, 7, ["octopus"])
    add("SPECIAL", rarity_map["SPECIAL"], "SUPPORT", "butterfly", "🦋", 10, 4, 6, ["butterfly"])

    # HIDDEN
    add("HIDDEN", rarity_map["HIDDEN"], "ATTACK", "dragon", "🐉", 16, 13, 5, ["dragon"])
    add("HIDDEN", rarity_map["HIDDEN"], "TANK", "trex", "🦖", 25, 7, 10, ["trex", "t-rex"])
    add("HIDDEN", rarity_map["HIDDEN"], "SUPPORT", "unicorn", "🦄", 14, 6, 8, ["unicorn"])

    return {a.animal_id: a for a in animals}


ANIMALS = build_animals()
LORE = {a.animal_id: f"Stories say the {a.animal_id.replace('_', ' ')} thrives in distant lands." for a in ANIMALS.values()}
ALIASES: Dict[str, str] = {}
for animal in ANIMALS.values():
    for alias in animal.aliases + [animal.emoji]:
        ALIASES[alias] = animal.animal_id


def build_foods() -> Dict[str, Food]:
    foods: List[Food] = []

    def add(
        food_id: str,
        emoji: str,
        rarity: str,
        cost: int,
        hp_bonus: int,
        atk_bonus: int,
        def_bonus: int,
        ability: str,
        aliases: List[str],
    ):
        foods.append(
            Food(
                food_id=food_id,
                emoji=emoji,
                rarity=rarity,
                cost=cost,
                hp_bonus=hp_bonus,
                atk_bonus=atk_bonus,
                def_bonus=def_bonus,
                ability=ability,
                aliases=aliases,
            )
        )

    add("apple", "🍎", "COMMON", 10, 2, 0, 0, "Sweet heal boosts HP slightly.", ["apple"])
    add("carrot", "🥕", "COMMON", 10, 1, 1, 0, "Crunchy bite adds small ATK.", ["carrot"])
    add("berry", "🫐", "COMMON", 12, 0, 1, 1, "Balanced snack for nimble critters.", ["berry"])
    add("bread", "🍞", "COMMON", 15, 2, 0, 1, "Comfort food with light defense.", ["bread"])
    add("corn", "🌽", "COMMON", 15, 1, 2, 0, "Energy burst improves strikes.", ["corn"])

    add("honey", "🍯", "UNCOMMON", 30, 3, 1, 1, "Sticky glaze toughens hides.", ["honey"])
    add("seaweed", "🪸", "UNCOMMON", 35, 2, 2, 1, "Ocean greens steady the mind.", ["seaweed", "kelp"])
    add("mushroom", "🍄", "UNCOMMON", 35, 1, 2, 2, "Forest spores sharpen senses.", ["mushroom", "shroom"])
    add("coconut", "🥥", "UNCOMMON", 40, 4, 0, 2, "Hard shell blocks blows.", ["coconut"])

    add("sushi", "🍣", "RARE", 80, 3, 4, 2, "Fresh cuts fuel precision strikes.", ["sushi"])
    add("cheese", "🧀", "RARE", 75, 5, 2, 1, "Rich flavor fortifies bodies.", ["cheese"])
    add("pepper", "🌶️", "RARE", 85, 0, 6, 1, "Spicy heat ignites fury.", ["pepper", "chili"])
    add("egg", "🥚", "RARE", 80, 4, 2, 2, "Protein pack grows resilient shells.", ["egg"])

    add("steak", "🥩", "EPIC", 200, 6, 6, 2, "Prime cut empowers champions.", ["steak"])
    add("ramen", "🍜", "EPIC", 210, 4, 5, 4, "Hearty bowl restores focus.", ["ramen", "noodles"])
    add("salmon", "🍣", "EPIC", 220, 5, 5, 3, "Omega boost sharpens instincts.", ["salmon"])
    add("truffle", "🍄", "EPIC", 230, 3, 6, 5, "Rare aroma inspires bravery.", ["truffle"])

    add("golden_apple", "🍏", "LEGENDARY", 500, 10, 6, 6, "Mythic fruit renews life.", ["gapple", "goldapple"])
    add("phoenix_pepper", "🪽", "LEGENDARY", 520, 4, 12, 4, "Flame-kissed spice scorches foes.", ["phoenixpepper", "firepepper"])
    add("royal_honey", "🍯", "LEGENDARY", 510, 8, 5, 8, "Regal nectar hardens armor.", ["royalhoney"])

    add("stardust", "✨", "SPECIAL", 900, 12, 10, 10, "Falling star radiance empowers all stats.", ["stardust"])
    add("moon_berry", "🌙", "SPECIAL", 880, 14, 8, 8, "Night bloom calms and heals.", ["moonberry"])

    add("dragons_feast", "🍖", "HIDDEN", 1500, 16, 16, 12, "Legendary banquet awakens ancient power.", ["dragonfeast", "dfeast"])
    add("unicorn_cake", "🍰", "HIDDEN", 1550, 14, 12, 14, "Shimmering icing shields allies.", ["unicorncake", "ucake"])
    add("abyssal_ink", "🪶", "HIDDEN", 1600, 12, 18, 10, "Void ink sharpens lethal focus.", ["ink", "abyssalink"])

    add("ancient_seed", "🪴", "SPECIAL", 950, 18, 6, 12, "Grows protective vines mid-battle.", ["ancientseed", "seed"])

    return {f.food_id: f for f in foods}


FOODS = build_foods()
FOOD_ALIASES: Dict[str, str] = {}
for food in FOODS.values():
    for alias in food.aliases + [food.emoji]:
        FOOD_ALIASES[alias] = food.food_id


DROP_TABLE: List[Tuple[float, str]] = [
    (62.0, "COMMON"),
    (24.0, "UNCOMMON"),
    (9.0, "RARE"),
    (3.0, "EPIC"),
    (1.2, "LEGENDARY"),
    (0.5, "SPECIAL"),
    (0.3, "HIDDEN"),
]

RARITY_SELL_VALUE = {
    "COMMON": 1,
    "UNCOMMON": 3,
    "RARE": 8,
    "EPIC": 20,
    "LEGENDARY": 60,
    "SPECIAL": 120,
    "HIDDEN": 250,
}


# ==============================
# Persistence
# ==============================


class DataStore:
    def __init__(self, path: str = DATA_FILE_PATH):
        self.path = path
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        dir_name = os.path.dirname(self.path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(self.path):
            initial_content = {"version": 3, "users": {}, "global": {"hatch_counts": {}}}
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(initial_content, f, indent=2)
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"❌ Failed to parse users.json: {exc}")
            raise RuntimeError("users.json is invalid. Fix the file before running the bot.")

        if "version" not in data or "users" not in data:
            raise RuntimeError("users.json is missing required keys. Aborting startup.")
        if data.get("version", 0) < 3:
            data["version"] = 3
            migrated_version = True
        else:
            migrated_version = False
        data.setdefault("global", {"hatch_counts": {}})
        global_data = data.setdefault("global", {})
        global_data.setdefault("hatch_counts", {})
        global_data.setdefault("owned_counts", {})
        global_data.setdefault("sold_counts", {})
        users = data.get("users", {})
        migrated = migrated_version or self._migrate_users(users)
        global_data["owned_counts"] = self._recalculate_owned_counts(users)
        data["users"] = users
        if migrated:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return data

    def _recalculate_owned_counts(self, users: Dict[str, Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for profile in users.values():
            zoo = profile.get("zoo", {})
            for animal_id, qty in zoo.items():
                if isinstance(qty, dict):
                    total = 0
                    for v in qty.values():
                        try:
                            total += max(0, int(v))
                        except (TypeError, ValueError):
                            continue
                else:
                    total = max(0, int(qty))
                counts[animal_id] = counts.get(animal_id, 0) + total
        return counts

    def _migrate_users(self, users: Dict[str, Dict]) -> bool:
        migrated = False
        for user_id, profile in users.items():
            if self._migrate_profile(user_id, profile):
                migrated = True
        return migrated

    def _normalize_zoo_entry(self, value) -> Dict[str, int]:
        if isinstance(value, dict):
            bucket = default_mutation_counts()
            for key, qty in value.items():
                try:
                    normalized = normalize_mutation_key(key)
                    qty_int = int(qty)
                except ValueError:
                    continue
                except TypeError:
                    continue
                bucket[normalized] = max(0, qty_int)
            return bucket
        try:
            return {"none": max(0, int(value))}
        except (ValueError, TypeError):
            return default_mutation_counts()

    def _migrate_profile(self, user_id: str, profile: Dict) -> bool:
        migrated = False
        if "user_id" not in profile:
            profile["user_id"] = user_id
            migrated = True
        if "coins" not in profile:
            profile["coins"] = 0
            migrated = True
        if "energy" not in profile:
            profile["energy"] = 0
            migrated = True
        if "zoo" not in profile:
            profile["zoo"] = {}
            migrated = True
        if "team" not in profile:
            profile["team"] = {"slot1": None, "slot2": None, "slot3": None}
            migrated = True
        if "foods" not in profile:
            profile["foods"] = {}
            migrated = True
        if "equipped_foods" not in profile:
            profile["equipped_foods"] = {"slot1": None, "slot2": None, "slot3": None}
            migrated = True
        if "equipped_food_wins" not in profile:
            profile["equipped_food_wins"] = {"slot1": 0, "slot2": 0, "slot3": 0}
            migrated = True
        if "cooldowns" not in profile:
            profile["cooldowns"] = {"hunt": 0.0, "battle": 0.0}
            migrated = True
        if "last_enemy_signature" not in profile:
            profile["last_enemy_signature"] = None
            migrated = True
        if "battles_won" not in profile:
            profile["battles_won"] = 0
            migrated = True

        zoo = profile.get("zoo", {})
        normalized_zoo: Dict[str, Dict[str, int]] = {}
        for animal_id, value in zoo.items():
            normalized_zoo[animal_id] = self._normalize_zoo_entry(value)
            if value != normalized_zoo[animal_id]:
                migrated = True
        profile["zoo"] = normalized_zoo

        team = profile.get("team", {})
        fixed_team: Dict[str, Optional[Dict[str, str]]] = {}
        for i in range(1, 4):
            slot = f"slot{i}"
            raw_value = team.get(slot)
            if isinstance(raw_value, str):
                slot_value = {"animal_id": raw_value, "mutation": "none"}
                migrated = True
            elif isinstance(raw_value, dict) and raw_value:
                mutation = raw_value.get("mutation", "none")
                try:
                    mutation = normalize_mutation_key(str(mutation))
                except ValueError:
                    mutation = "none"
                slot_value = {"animal_id": raw_value.get("animal_id"), "mutation": mutation}
            else:
                slot_value = None

            if slot_value and slot_value.get("animal_id") in normalized_zoo:
                bucket = normalized_zoo[slot_value["animal_id"]]
                if bucket.get(slot_value["mutation"], 0) <= 0:
                    for mut in MUTATIONS:
                        if bucket.get(mut, 0) > 0:
                            slot_value["mutation"] = mut
                            migrated = True
                            break
                    else:
                        slot_value = None
                        migrated = True
            elif slot_value:
                slot_value = None
                migrated = True
            fixed_team[slot] = slot_value
        profile["team"] = fixed_team
        return migrated

    def _default_profile(self, user_id: str) -> Dict:
        team = {"slot1": None, "slot2": None, "slot3": None}
        return {
            "user_id": user_id,
            "coins": 0,
            "energy": 0,
            "zoo": {},
            "team": team,
            "foods": {},
            "equipped_foods": {"slot1": None, "slot2": None, "slot3": None},
            "equipped_food_wins": {"slot1": 0, "slot2": 0, "slot3": 0},
            "cooldowns": {"hunt": 0.0, "battle": 0.0},
            "last_enemy_signature": None,
            "battles_won": 0,
        }

    def load_profile(self, user_id: str) -> Dict:
        if user_id not in self.data.get("users", {}):
            self.data["users"][user_id] = self._default_profile(user_id)
            self._write_data()
        profile = self.data["users"][user_id]
        if self._migrate_profile(user_id, profile):
            self._write_data()
        return profile

    def save_profile(self, profile: Dict) -> None:
        self.data.setdefault("users", {})[profile["user_id"]] = profile
        self._write_data()

    def record_hatch(self, animal_id: str) -> None:
        global_data = self.data.setdefault("global", {})
        hatch_counts = global_data.setdefault("hatch_counts", {})
        hatch_counts[animal_id] = hatch_counts.get(animal_id, 0) + 1

    def adjust_owned_count(self, animal_id: str, delta: int) -> None:
        global_data = self.data.setdefault("global", {})
        owned_counts = global_data.setdefault("owned_counts", {})
        owned_counts[animal_id] = max(0, owned_counts.get(animal_id, 0) + delta)

    def record_sale(self, animal_id: str, amount: int) -> None:
        if amount <= 0:
            return
        global_data = self.data.setdefault("global", {})
        sold_counts = global_data.setdefault("sold_counts", {})
        sold_counts[animal_id] = sold_counts.get(animal_id, 0) + amount

    def _write_data(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)


store = DataStore()
DAILY_COOLDOWNS: Dict[str, float] = {}


# ==============================
# Utility helpers
# ==============================


def resolve_animal(query: str) -> Optional[Animal]:
    key = query.strip().lower()
    animal_id = ALIASES.get(key)
    if animal_id:
        return ANIMALS[animal_id]
    return None


def resolve_food(query: str) -> Optional[Food]:
    key = query.strip().lower()
    food_id = FOOD_ALIASES.get(key)
    if food_id:
        return FOODS[food_id]
    return None


def chunk_text_blocks(blocks: List[str], limit: int = 1024, separator: str = "\n\n") -> List[str]:
    chunks: List[str] = []
    current: List[str] = []
    current_length = 0
    for block in blocks:
        block_length = len(block)
        sep_length = len(separator) if current else 0
        if current and current_length + sep_length + block_length > limit:
            chunks.append(separator.join(current))
            current = [block]
            current_length = block_length
        else:
            current.append(block)
            current_length += sep_length + block_length
    if current:
        chunks.append(separator.join(current))
    return chunks


def now() -> float:
    return time.time()


def format_cooldown(seconds_left: float) -> str:
    seconds = int(max(0, seconds_left))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def hp_bar(current: int, maximum: int) -> str:
    filled = max(0, min(10, round(10 * current / maximum))) if maximum else 0
    return "█" * filled + "░" * (10 - filled)


SUPERSCRIPT_MAP = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}


def superscript_number(num: int) -> str:
    num_str = str(max(0, num))
    if len(num_str) == 1:
        return SUPERSCRIPT_MAP["0"] + SUPERSCRIPT_MAP[num_str]
    return "".join(SUPERSCRIPT_MAP[d] for d in num_str)


def reserved_count(team: Dict[str, Optional[Dict[str, str]]], animal_id: str, mutation: str) -> int:
    mutation = normalize_mutation_key(mutation)
    total = 0
    for slot in team.values():
        if not slot or not isinstance(slot, dict):
            continue
        if slot.get("animal_id") == animal_id and slot.get("mutation") == mutation:
            total += 1
    return total


def reserved_species_count(team: Dict[str, Optional[Dict[str, str]]], animal_id: str) -> int:
    return sum(
        reserved_count(team, animal_id, mutation) for mutation in MUTATIONS
    )


def sellable_amount(profile: Dict, animal_id: str, mutation: str) -> int:
    owned = get_owned_count(profile, animal_id, mutation)
    reserved = reserved_count(profile.get("team", {}), animal_id, mutation)
    return max(0, owned - reserved)


def sellable_species_amount(profile: Dict, animal_id: str) -> int:
    owned = total_owned_species(profile, animal_id)
    reserved = reserved_species_count(profile.get("team", {}), animal_id)
    return max(0, owned - reserved)


def roll_fusion_result(input_mutation: str) -> Tuple[str, int]:
    mutation = normalize_mutation_key(input_mutation)
    roll = random.random() * 100

    if mutation == "none":
        if roll < 50:
            return "golden", 1
        if roll < 75:
            return "diamond", 1
        if roll < 95:
            return "emerald", 1
        return "rainbow", 1

    if mutation == "golden":
        if roll < 50:
            return "diamond", 1
        if roll < 90:
            return "emerald", 1
        return "rainbow", 1

    if mutation == "diamond":
        if roll < 75:
            return "emerald", 1
        return "rainbow", 1

    if mutation == "emerald":
        if roll < 50:
            return "emerald", 3
        return "rainbow", 1

    raise ValueError("Rainbow mutation cannot be fused")


def add_food(profile: Dict, food_id: str, amount: int) -> None:
    profile.setdefault("foods", {})
    profile["foods"][food_id] = profile["foods"].get(food_id, 0) + amount


def rarity_header(rarity: str) -> str:
    symbol = dict(RARITY_ORDER)[rarity]
    return f"{symbol} {rarity}"


def coins_reward(enemy_multiplier: float) -> int:
    base = 10
    scaled = round(base * enemy_multiplier)
    return max(5, scaled)


def enemy_signature(team: Dict[str, Animal], mutations: Optional[Dict[str, str]] = None) -> str:
    parts: List[str] = []
    for i in range(1, 4):
        slot = f"slot{i}"
        mut = ""
        if mutations:
            try:
                mut_key = normalize_mutation_key(mutations.get(slot, "none"))
                mut = f":{mut_key}"
            except ValueError:
                mut = ""
        parts.append(f"{team[slot].animal_id}{mut}")
    return "|".join(parts)


def team_def_alive(team_hp: Dict[str, int], team_animals: Dict[str, Animal]) -> int:
    total = 0
    for i in range(1, 4):
        slot = f"slot{i}"
        if team_hp[slot] > 0:
            total += team_animals[slot].defense
    return total


def pick_rarity() -> str:
    roll = random.random() * 100
    cumulative = 0.0
    for chance, rarity in DROP_TABLE:
        cumulative += chance
        if roll <= cumulative:
            return rarity
    return DROP_TABLE[-1][1]


def random_animal_by_rarity_and_role(allowed_indices: List[int], role: str) -> Animal:
    candidates = [a for a in ANIMALS.values() if a.role == role and a.rarity_index in allowed_indices]
    return random.choice(candidates)


def power(animal: Animal) -> float:
    return animal.hp * 1.0 + animal.atk * 1.5 + animal.defense * 1.2


def food_power(food: Optional[Food]) -> float:
    if not food:
        return 0.0
    return food.hp_bonus * 1.0 + food.atk_bonus * 1.5 + food.def_bonus * 1.2


def mutation_multiplier_value(mutation: str) -> float:
    meta = MUTATION_META.get(normalize_mutation_key(mutation), MUTATION_META["none"])
    return float(meta.get("ability_multiplier", 1.0))


def effective_power(animal: Animal, food: Optional[Food], mutation_multiplier: float) -> float:
    return (power(animal) + food_power(food)) * mutation_multiplier


def calculate_team_power(
    animals: Dict[str, Animal],
    foods: Dict[str, Optional[Food]],
    mutations: Dict[str, str],
) -> float:
    total = 0.0
    for i in range(1, 4):
        slot = f"slot{i}"
        mutation_multiplier = mutation_multiplier_value(mutations.get(slot, "none"))
        total += effective_power(animals[slot], foods.get(slot), mutation_multiplier)
    return total


def random_enemy_food(animal: Animal) -> Optional[Food]:
    if random.random() >= 0.35:
        return None
    animal_idx = RARITY_INDEX.get(animal.rarity, 0)
    candidates = [
        food
        for food in FOODS.values()
        if abs(RARITY_INDEX.get(food.rarity, 0) - animal_idx) <= 1
    ]
    if not candidates:
        candidates = list(FOODS.values())
    return random.choice(candidates)


def random_enemy_mutation() -> str:
    roll = random.random()
    if roll < 0.55:
        return "none"
    if roll < 0.75:
        return "golden"
    if roll < 0.9:
        return "diamond"
    if roll < 0.97:
        return "emerald"
    return "rainbow"


MUTATION_STRENGTH_ORDER = sorted(MUTATIONS, key=lambda m: mutation_multiplier_value(m))


def _downgrade_mutation(mutations: Dict[str, str]) -> bool:
    sorted_slots = sorted(
        ((slot, mutation_multiplier_value(mutation)) for slot, mutation in mutations.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    for slot, current_multiplier in sorted_slots:
        order_idx = MUTATION_STRENGTH_ORDER.index(normalize_mutation_key(mutations[slot]))
        if order_idx > 0 and current_multiplier > 1.0:
            mutations[slot] = MUTATION_STRENGTH_ORDER[order_idx - 1]
            return True
    return False


def _upgrade_mutation(mutations: Dict[str, str]) -> bool:
    sorted_slots = sorted(
        ((slot, mutation_multiplier_value(mutation)) for slot, mutation in mutations.items()),
        key=lambda item: item[1],
    )
    for slot, _mult in sorted_slots:
        order_idx = MUTATION_STRENGTH_ORDER.index(normalize_mutation_key(mutations[slot]))
        if order_idx < len(MUTATION_STRENGTH_ORDER) - 1:
            mutations[slot] = MUTATION_STRENGTH_ORDER[order_idx + 1]
            return True
    return False


def _remove_highest_food(foods: Dict[str, Optional[Food]]) -> bool:
    slot_to_remove = None
    highest = -1.0
    for slot, food in foods.items():
        fp = food_power(food)
        if food and fp > highest:
            highest = fp
            slot_to_remove = slot
    if slot_to_remove:
        foods[slot_to_remove] = None
        return True
    return False


def _add_missing_food(animals: Dict[str, Animal], foods: Dict[str, Optional[Food]]) -> bool:
    empty_slots = [slot for slot, food in foods.items() if food is None]
    if not empty_slots:
        return False
    slot = random.choice(empty_slots)
    foods[slot] = random_enemy_food(animals[slot])
    return foods[slot] is not None


def adjust_enemy_team(
    animals: Dict[str, Animal],
    foods: Dict[str, Optional[Food]],
    mutations: Dict[str, str],
    allowed_indices: List[int],
    target_min: float,
    target_max: float,
) -> float:
    for _ in range(350):
        current_power = calculate_team_power(animals, foods, mutations)
        if target_min <= current_power <= target_max:
            return current_power
        if current_power > target_max:
            if _remove_highest_food(foods):
                continue
            if _downgrade_mutation(mutations):
                continue
        else:
            if _add_missing_food(animals, foods):
                continue
            if _upgrade_mutation(mutations):
                continue
        slot = random.choice(list(animals.keys()))
        animals[slot] = random_animal_by_rarity_and_role(allowed_indices, animals[slot].role)
        foods[slot] = None if current_power > target_max else random_enemy_food(animals[slot])
        mutations[slot] = "none" if current_power > target_max else random_enemy_mutation()

    # Final enforcement to guarantee constraints
    strongest_food = max(FOODS.values(), key=food_power)
    weakest_index = min(allowed_indices)
    strongest_index = max(allowed_indices)

    for _ in range(200):
        current_power = calculate_team_power(animals, foods, mutations)
        if target_min <= current_power <= target_max:
            break
        if current_power > target_max:
            if _remove_highest_food(foods):
                continue
            if _downgrade_mutation(mutations):
                continue
            slot = random.choice(list(animals.keys()))
            animals[slot] = random_animal_by_rarity_and_role([weakest_index], animals[slot].role)
            foods[slot] = None
            mutations[slot] = "none"
        else:
            if _add_missing_food(animals, foods):
                continue
            if _upgrade_mutation(mutations):
                continue
            slot = random.choice(list(animals.keys()))
            animals[slot] = random_animal_by_rarity_and_role([strongest_index], animals[slot].role)
            foods[slot] = strongest_food
            mutations[slot] = MUTATION_STRENGTH_ORDER[-1]

    return calculate_team_power(animals, foods, mutations)


def apply_food(animal: Animal, food: Optional[Food]) -> Tuple[int, int, int]:
    hp = animal.hp + (food.hp_bonus if food else 0)
    atk = animal.atk + (food.atk_bonus if food else 0)
    defense = animal.defense + (food.def_bonus if food else 0)
    return hp, atk, defense


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        dev_guild = discord.Object(id=DEV_GUILD_ID)

        # Ensure the guild command set is refreshed without touching global commands.
        self.tree.clear_commands(guild=dev_guild)
        synced = await self.tree.sync(guild=dev_guild)
        print(f"⚡ Synced {len(synced)} guild slash commands")


client = MyClient()


DEV_GUILD_ID = 1452648204519739483  # your server


def build_help_embed(page: int) -> Optional[discord.Embed]:
    header_text = "Use slash commands (/) to interact with the bot."

    if page == 1:
        embed = discord.Embed(
            title="📘 Emoji Zoo Battle Bot — Help (1/2)",
            description=(
                f"{header_text}\n\n"
                "Collect animals, build teams, and battle enemies with hidden difficulty."
            ),
            color=0x9B59B6,
        )
        embed.add_field(
            name="[🎯 Core Loop]",
            value=(
                "1️⃣ Claim daily rewards  \n"
                "2️⃣ Win battles to gain energy (battle results use embeds)  \n"
                "3️⃣ Hunt animals using coins + energy  \n"
                "4️⃣ Equip foods to boost stats  \n"
                "5️⃣ Build a Tank / Attack / Support team  \n"
                "6️⃣ Repeat and grow your zoo  "
            ),
            inline=False,
        )
        embed.add_field(
            name="[💰 Currencies]",
            value=(
                "💰 Coins  \n"
                "• Used for hunting animals  \n\n"
                "🔋 Energy  \n"
                "• Required for hunting  \n"
                "• Gained from battle wins  \n"
                "• NO LIMIT — stacks forever  "
            ),
            inline=False,
        )
        embed.add_field(
            name="[🧾 Commands]",
            value=(
                "/daily        → daily rewards  \n"
                "/balance      → show coins & energy  \n"
                "/zoo          → view animals (counts only)  \n"
                "/index        → global animal index (all drop rates & stats)  \n"
                "/stats <x>    → view animal stats & lore  \n"
                "/team view    → see your current team  \n"
                "/team add     → build your team  \n"
                "/team remove  → remove from team  \n"
                "/hunt <amt>   → hunt animals  \n"
                "/battle       → fight enemy teams (embed results)  \n"
                "/shop         → browse foods  \n"
                "/buy <food>   → buy a food by emoji or alias  \n"
                "/inv          → view owned foods  \n"
                "/use <food> <pos> → equip food (replaces old)  \n"
                "/sell <x> <n> → sell animals or food"
            ),
            inline=False,
        )
        embed.add_field(
            name="[🐾 Animal Input]",
            value=(
                "Animals can be referenced by:\n"
                "• Emoji (🐘)\n"
                "• Alias (elephant)"
            ),
            inline=False,
        )
        embed.set_footer(text="Use /help 2 for battle and food rules")
        return embed

    if page == 2:
        embed = discord.Embed(
            title="📘 Emoji Zoo Battle Bot — Help (2/2)",
            description=header_text,
            color=0x3498DB,
        )
        embed.add_field(
            name="[🧑‍🤝‍🧑 Team Slots]",
            value=(
                "Slot 1 → 🛡️ Tank only  \n"
                "Slot 2 → ⚔️ Attack only  \n"
                "Slot 3 → 🧪 Support only  "
            ),
            inline=False,
        )
        embed.add_field(
            name="[⚔️ Battle Flow]",
            value=(
                "• Results are sent as clean embeds  \n"
                "• Enemy scales to your team and equipped food power  \n"
                "• Difficulty shown as text hint (Weaker / Balanced / Tough)"
            ),
            inline=False,
        )
        embed.add_field(
            name="[📘 Animal Index]",
            value=(
                "• /index shows every animal regardless of ownership  \n"
                "• Displays drop rates, base stats, and global hatch counts  \n"
                "• Use /stats <animal> for detailed view (lore, foods)  \n"
                "• /zoo remains your personal collection counts"
            ),
            inline=False,
        )
        embed.add_field(
            name="[🍽️ Food System]",
            value=(
                "• 25 foods with matching rarities to animals  \n"
                "• Equip with /use <food> <slot> (replaces old food instantly)  \n"
                "• Food boosts stats in battle and enemy scaling  \n"
                "• Check stock with /shop and your bag with /inv"
            ),
            inline=False,
        )
        embed.add_field(
            name="[💰 Selling]",
            value=(
                "• /sell supports animals and food  \n"
                "• Equipped food cannot be sold (replace it first)  \n"
                "• Food sale value drops by 1% per battle win (50% floor)"
            ),
            inline=False,
        )
        embed.add_field(
            name="[🌱 Hatch Counters]",
            value="/stats now shows how many times each animal hatched globally.",
            inline=False,
        )
        embed.set_footer(text="Build smart teams — roles matter. Equip food before fighting!")
        return embed

    return None


@client.tree.command(name="help", description="📘 View the Emoji Zoo help pages")
@app_commands.describe(page="Help page number (1 or 2)")
async def help_command(interaction: discord.Interaction, page: int = 1):
    embed = build_help_embed(page)
    if not embed:
        await interaction.response.send_message(
            "❌ Invalid page. Choose 1 or 2.", ephemeral=True
        )
        return
    await interaction.response.send_message(embed=embed)


def build_index_embed() -> discord.Embed:
    description = (
        "Browse animals by rarity. Use the filters to see what you own, what you're missing,"
        " or everything at once."
    )
    embed = discord.Embed(title="📘 Animal Index", description=description, color=0x2980B9)
    embed.set_footer(text="Buttons: ⬅️ / ➡️ to change rarity • Filters below")
    return embed


def format_animal_block(animal: Animal, owned_amount: int) -> str:
    owned_indicator = "🟢" if owned_amount > 0 else "🔴"
    spawn_chance = spawn_chance_for_animal(animal)
    hatched, owned_global, sold_global = global_animal_stats(animal.animal_id)
    return (
        f"{owned_indicator} {animal.emoji} {animal.animal_id}\n"
        f"Role: {ROLE_EMOJI[animal.role]} {animal.role}\n\n"
        f"❤️ HP: {animal.hp}\n"
        f"⚔️ ATK: {animal.atk}\n"
        f"🛡️ DEF: {animal.defense}\n\n"
        f"🛡️ Team DEF Aura: +{animal.defense}\n"
        f"🌱 Hatched globally: {hatched}\n"
        f"🎯 Spawn Chance: {spawn_chance:.2f}%\n"
        f"🌍 Owned Globally: {owned_global}\n"
        f"💰 Sold Globally: {sold_global}\n"
        f"💵 Value: {RARITY_SELL_VALUE[animal.rarity]} coins\n\n"
        f"📜 Lore: {LORE.get(animal.animal_id, 'Mysterious origins.')}"
    )


class IndexView(discord.ui.View):
    def __init__(self, user_id: int, profile: Dict):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.profile = profile
        self.rarity_position = 0
        self.filter_mode = "all"
        self._sync_button_states()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the command user can use these buttons.", ephemeral=True)
            return False
        return True

    def _sync_button_states(self) -> None:
        self.previous_button.disabled = self.rarity_position == 0
        self.next_button.disabled = self.rarity_position == len(RARITY_ORDER) - 1
        self.all_button.style = (
            discord.ButtonStyle.primary if self.filter_mode == "all" else discord.ButtonStyle.secondary
        )
        self.owned_button.style = (
            discord.ButtonStyle.primary if self.filter_mode == "owned" else discord.ButtonStyle.secondary
        )
        self.not_owned_button.style = (
            discord.ButtonStyle.primary if self.filter_mode == "not_owned" else discord.ButtonStyle.secondary
        )

    def _build_page(self) -> discord.Embed:
        self.profile = store.load_profile(str(self.user_id))
        rarity, emoji = RARITY_ORDER[self.rarity_position]
        animals = rarity_animals(rarity)
        blocks: List[str] = []
        for animal in animals:
            owned_amount = self.profile.get("zoo", {}).get(animal.animal_id, 0)
            if self.filter_mode == "owned" and owned_amount <= 0:
                continue
            if self.filter_mode == "not_owned" and owned_amount > 0:
                continue
            blocks.append(format_animal_block(animal, owned_amount))

        embed = build_index_embed()
        filter_titles = {"all": "All", "owned": "Owned", "not_owned": "Not Owned"}
        embed.title = f"📘 Animal Index — {emoji} {rarity.title()}"
        display_blocks = blocks or ["No animals match this filter."]
        chunk: List[str] = []
        chunk_length = 0
        for block in display_blocks:
            block_length = len(block)
            separator_length = 2 if chunk else 0
            if chunk and chunk_length + separator_length + block_length > 1024:
                embed.add_field(
                    name=f"Filter: {filter_titles[self.filter_mode]}" if not embed.fields else "Continued",
                    value="\n\n".join(chunk),
                    inline=False,
                )
                chunk = [block]
                chunk_length = block_length
            else:
                if chunk:
                    chunk_length += separator_length
                chunk.append(block)
                chunk_length += block_length

        if chunk:
            embed.add_field(
                name=f"Filter: {filter_titles[self.filter_mode]}" if not embed.fields else "Continued",
                value="\n\n".join(chunk),
                inline=False,
            )
        return embed

    async def _update_message(self, interaction: discord.Interaction) -> None:
        self._sync_button_states()
        await interaction.response.edit_message(embed=self._build_page(), view=self)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.rarity_position = max(0, self.rarity_position - 1)
        await self._update_message(interaction)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.rarity_position = min(len(RARITY_ORDER) - 1, self.rarity_position + 1)
        await self._update_message(interaction)

    @discord.ui.button(label="All", style=discord.ButtonStyle.secondary)
    async def all_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.filter_mode = "all"
        await self._update_message(interaction)

    @discord.ui.button(label="Owned", style=discord.ButtonStyle.secondary)
    async def owned_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.filter_mode = "owned"
        await self._update_message(interaction)

    @discord.ui.button(label="Not Owned", style=discord.ButtonStyle.secondary)
    async def not_owned_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.filter_mode = "not_owned"
        await self._update_message(interaction)


@client.tree.command(name="index", description="📘 Browse all animals and their drop rates")
async def index(interaction: discord.Interaction):
    profile = store.load_profile(str(interaction.user.id))
    view = IndexView(interaction.user.id, profile)
    await interaction.response.send_message(embed=view._build_page(), view=view)


def rarity_drop_rate_map() -> Dict[str, float]:
    return {rarity: chance for chance, rarity in DROP_TABLE}


def rarity_animals(rarity: str) -> List[Animal]:
    return sorted([a for a in ANIMALS.values() if a.rarity == rarity], key=lambda a: a.animal_id)


def spawn_chance_for_animal(animal: Animal) -> float:
    rarity_chance = rarity_drop_rate_map().get(animal.rarity, 0.0)
    animals_in_rarity = len(rarity_animals(animal.rarity))
    if animals_in_rarity == 0:
        return 0.0
    return rarity_chance / animals_in_rarity


def global_animal_stats(animal_id: str) -> Tuple[int, int, int]:
    global_data = store.data.get("global", {})
    hatch_counts = global_data.get("hatch_counts", {})
    owned_counts = global_data.get("owned_counts", {})
    sold_counts = global_data.get("sold_counts", {})
    return (
        hatch_counts.get(animal_id, 0),
        owned_counts.get(animal_id, 0),
        sold_counts.get(animal_id, 0),
    )


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    content = message.content.strip()
    lowered = content.lower()
    if not lowered:
        return

    if lowered.startswith("-data"):
        store._write_data()
        await message.channel.send(
            "📂 Current users.json backup. Replace your local file with this copy.",
            file=discord.File(DATA_FILE_PATH, filename="users.json"),
        )


@client.tree.command(name="balance", description="💼 Check your coins and energy")
async def balance(interaction: discord.Interaction):
    profile = store.load_profile(str(interaction.user.id))
    embed = discord.Embed(title="💼 Your Balance", color=0xF1C40F)
    embed.add_field(name="💰 Coins", value=str(profile["coins"]), inline=False)
    embed.add_field(name="🔋 Energy", value=str(profile["energy"]), inline=False)
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="daily", description="🎁 Claim your daily coins reward")
async def daily(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    profile = store.load_profile(user_id)
    now_ts = now()
    cooldown_until = DAILY_COOLDOWNS.get(user_id, 0.0)
    if cooldown_until > now_ts:
        wait = format_cooldown(cooldown_until - now_ts)
        embed = discord.Embed(
            title="⏳ Daily Cooldown",
            description=(
                "You already claimed your daily reward.\n"
                f"Try again in {wait}."
            ),
            color=0xE74C3C,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    profile["coins"] += 100
    profile["energy"] += 40
    store.save_profile(profile)
    DAILY_COOLDOWNS[user_id] = now_ts + 24 * 3600
    embed = discord.Embed(title="🎁 Daily Reward", color=0x2ECC71)
    embed.add_field(name="💰 Coins", value="+100", inline=False)
    embed.add_field(name="🔋 Energy", value="+40", inline=False)
    embed.set_footer(text="Come back in 24 hours")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="zoo", description="🗂️ View your zoo inventory counts")
async def zoo(interaction: discord.Interaction):
    profile = store.load_profile(str(interaction.user.id))
    lines: List[str] = []
    for rarity, symbol in RARITY_ORDER:
        animals = [a for a in ANIMALS.values() if a.rarity == rarity]
        animals.sort(key=lambda a: a.animal_id)
        entries = []
        for animal in animals:
            amount = total_owned_species(profile, animal.animal_id)
            if amount <= 0:
                continue
            entries.append(f"{animal.emoji} {superscript_number(amount)}")
        if entries:
            lines.append(f"{symbol} {rarity.capitalize()}\n" + "  ".join(entries))
    await interaction.response.send_message("\n\n".join(lines) if lines else "Your zoo is empty.")


@client.tree.command(name="shop", description="🛒 Browse the food store")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛒 Food Shop",
        description="All foods are always in stock. Pick a snack and equip it with /use.",
        color=0xF1C40F,
    )
    for rarity, symbol in RARITY_ORDER:
        foods = [f for f in FOODS.values() if f.rarity == rarity]
        if not foods:
            continue
        foods.sort(key=lambda f: f.cost)
        value_lines = []
        for food in foods:
            value_lines.append(
                f"{food.emoji} {food.food_id.replace('_', ' ')} — Cost: {food.cost} | {food.ability}"
            )
        embed.add_field(name=f"{symbol} {rarity.title()}", value="\n".join(value_lines), inline=False)
    embed.set_footer(text="Use /use <food> <slot> to equip")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="buy", description="🧺 Buy a food by emoji or alias")
@app_commands.describe(food="Food emoji or alias")
async def buy(interaction: discord.Interaction, food: str):
    food_obj = resolve_food(food)
    if not food_obj:
        await interaction.response.send_message(
            "❌ Unknown food. Try an emoji or alias listed in /shop.", ephemeral=True
        )
        return

    profile = store.load_profile(str(interaction.user.id))
    if profile["coins"] < food_obj.cost:
        await interaction.response.send_message(
            f"❌ Not enough coins. {food_obj.emoji} costs {food_obj.cost} coins.",
            ephemeral=True,
        )
        return

    profile["coins"] -= food_obj.cost
    profile["foods"][food_obj.food_id] = profile["foods"].get(food_obj.food_id, 0) + 1
    store.save_profile(profile)

    embed = discord.Embed(
        title="✅ Purchase Successful",
        description=f"You bought {food_obj.emoji} {food_obj.food_id.replace('_', ' ')}.",
        color=0x2ECC71,
    )
    embed.add_field(name="Cost", value=f"- {food_obj.cost} coins", inline=False)
    embed.add_field(name="Coins Left", value=str(profile["coins"]), inline=False)
    embed.set_footer(text="Equip it with /use <food> <slot>")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="inv", description="🎒 View your food inventory")
async def inv(interaction: discord.Interaction):
    profile = store.load_profile(str(interaction.user.id))
    embed = discord.Embed(title="🎒 Your Foods", color=0x95A5A6)
    if not profile["foods"]:
        embed.description = "You don't own any food. Visit /shop to buy some."
    else:
        for rarity, symbol in RARITY_ORDER:
            entries = []
            for food_id, qty in profile["foods"].items():
                food = FOODS.get(food_id)
                if food and food.rarity == rarity and qty > 0:
                    entries.append(f"{food.emoji} {food.food_id.replace('_', ' ')} x{qty}")
            if entries:
                embed.add_field(name=f"{symbol} {rarity.title()}", value="\n".join(entries), inline=False)
    embed.set_footer(text="Equip foods onto your team with /use")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="use", description="🍽️ Equip a food onto a team slot")
@app_commands.describe(food="Food emoji or alias", pos="Team slot (1-3)")
async def use_food(interaction: discord.Interaction, food: str, pos: int):
    if pos not in (1, 2, 3):
        await interaction.response.send_message("❌ Invalid slot. Choose 1, 2, or 3.", ephemeral=True)
        return
    food_obj = resolve_food(food)
    if not food_obj:
        await interaction.response.send_message("❌ Unknown food. Try an emoji or alias.", ephemeral=True)
        return
    profile = store.load_profile(str(interaction.user.id))
    owned = profile["foods"].get(food_obj.food_id, 0)
    if owned <= 0:
        await interaction.response.send_message(
            "❌ You don't own that food. Buy it in /shop first.", ephemeral=True
        )
        return
    slot_key = f"slot{pos}"
    previous_food = profile["equipped_foods"].get(slot_key)
    if previous_food:
        tip = f"Replaced {FOODS[previous_food].emoji} {previous_food}. Old food was destroyed."
    else:
        tip = ""
    profile["equipped_foods"][slot_key] = food_obj.food_id
    profile["equipped_food_wins"][slot_key] = 0
    profile["foods"][food_obj.food_id] = max(0, owned - 1)
    store.save_profile(profile)
    embed = discord.Embed(
        title="🍽️ Food Equipped",
        description=f"Slot {pos} now has {food_obj.emoji} {food_obj.food_id.replace('_', ' ')}.",
        color=0x2ECC71,
    )
    embed.add_field(name="Ability", value=food_obj.ability, inline=False)
    if tip:
        embed.set_footer(text=tip)
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="stats", description="📊 Show stats for an animal (emoji or alias)")
@app_commands.describe(animal="Emoji or alias of the animal")
async def stats(interaction: discord.Interaction, animal: str):
    a = resolve_animal(animal)
    if not a:
        await interaction.response.send_message(
            "❌ Unknown animal\nTry an emoji or alias.", ephemeral=True
        )
        return
    rarity_symbol = dict(RARITY_ORDER)[a.rarity]
    hatched, owned_global, sold_global = global_animal_stats(a.animal_id)
    spawn_chance = spawn_chance_for_animal(a)
    msg = (
        f"{rarity_symbol} {a.emoji} {a.animal_id}\n"
        f"Role: {ROLE_EMOJI[a.role]} {a.role}\n\n"
        f"❤️ HP: {a.hp}\n"
        f"⚔️ ATK: {a.atk}\n"
        f"🛡️ DEF: {a.defense}\n\n"
        f"🛡️ Team DEF Aura: +{a.defense}\n"
        f"🌱 Hatched globally: {hatched}\n"
        f"🎯 Spawn Chance: {spawn_chance:.2f}%\n"
        f"🌍 Owned Globally: {owned_global}\n"
        f"💰 Sold Globally: {sold_global}\n"
        f"💵 Value: {RARITY_SELL_VALUE[a.rarity]} coins\n\n"
        f"📜 Lore: {LORE.get(a.animal_id, 'Mysterious origins.')}"
    )
    await interaction.response.send_message(msg)


class TeamCommands(app_commands.Group):
    def __init__(self):
        super().__init__(name="team", description="🧭 Manage your battle team slots")

    @app_commands.command(name="view", description="🧑‍🤝‍🧑 View your current team")
    async def view(self, interaction: discord.Interaction):
        profile = store.load_profile(str(interaction.user.id))
        embed = discord.Embed(
            title="🧑‍🤝‍🧑 Your Team",
            description="Your active battle team.\nSlot order matters.",
            color=0x9B59B6,
        )
        slot_info = {
            1: ("slot1", "🛡️ Tank"),
            2: ("slot2", "⚔️ Attack"),
            3: ("slot3", "🧪 Support"),
        }
        total_hp = 0
        total_atk = 0
        total_def = 0
        for idx, (slot_key, label) in slot_info.items():
            slot_value = profile["team"].get(slot_key)
            animal_id = slot_value.get("animal_id") if isinstance(slot_value, dict) else None
            if animal_id:
                animal = ANIMALS[animal_id]
                total_hp += animal.hp
                total_atk += animal.atk
                total_def += animal.defense
                animal_name = animal.animal_id.replace("_", " ").title()
                embed.add_field(
                    name=f"Slot {idx} — {label}",
                    value=(
                        f"{animal.emoji} {animal_name}\n"
                        f"❤️ HP: {animal.hp}\n"
                        f"⚔️ ATK: {animal.atk}\n"
                        f"🛡️ DEF: {animal.defense}"
                    ),
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"Slot {idx} — {label}",
                    value="❌ Empty Slot\nUse /team add <animal> <slot>",
                    inline=False,
                )

        embed.add_field(
            name="TEAM SUMMARY",
            value=(
                f"🛡️ Total Team DEF: {total_def}\n"
                f"❤️ Total Team HP: {total_hp}\n"
                f"⚔️ Total Team ATK: {total_atk}"
            ),
            inline=False,
        )
        embed.set_footer(text="Slot order: Tank → Attack → Support")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add", description="➕ Assign an animal to a team slot")
    @app_commands.describe(animal="Emoji or alias", pos="Team slot (1=TANK, 2=ATTACK, 3=SUPPORT)")
    async def add(self, interaction: discord.Interaction, animal: str, pos: int):
        if pos not in (1, 2, 3):
            await interaction.response.send_message(
                "❌ Invalid slot\nSlot must be 1, 2, or 3.", ephemeral=True
            )
            return
        a = resolve_animal(animal)
        if not a:
            await interaction.response.send_message(
                "❌ Unknown animal\nTry an emoji or alias.", ephemeral=True
            )
            return
        role_requirement = {1: "TANK", 2: "ATTACK", 3: "SUPPORT"}
        if a.role != role_requirement[pos]:
            await interaction.response.send_message(
                f"❌ Invalid placement\nSlot {pos} requires a {role_requirement[pos]}.",
                ephemeral=True,
            )
            return

        profile = store.load_profile(str(interaction.user.id))
        available_total = sellable_species_amount(profile, a.animal_id)
        if available_total <= 0:
            await interaction.response.send_message(
                "❌ You don't own that animal yet.", ephemeral=True
            )
            return
        chosen_mutation = None
        for mutation in MUTATIONS:
            if sellable_amount(profile, a.animal_id, mutation) > 0:
                chosen_mutation = mutation
                break
        if not chosen_mutation:
            await interaction.response.send_message(
                "❌ That animal is fully reserved on your team.", ephemeral=True
            )
            return

        profile["team"][f"slot{pos}"] = {"animal_id": a.animal_id, "mutation": chosen_mutation}
        store.save_profile(profile)
        await interaction.response.send_message(
            f"✅ TEAM UPDATED\nSlot {pos}: {ROLE_EMOJI[a.role]} {a.emoji} {a.animal_id}"
        )

    @app_commands.command(name="remove", description="➖ Clear a team slot")
    @app_commands.describe(pos="Team slot to clear (1-3)")
    async def remove(self, interaction: discord.Interaction, pos: int):
        if pos not in (1, 2, 3):
            await interaction.response.send_message(
                "❌ Invalid slot\nSlot must be 1, 2, or 3.", ephemeral=True
            )
            return
        profile = store.load_profile(str(interaction.user.id))
        profile["team"][f"slot{pos}"] = None
        store.save_profile(profile)
        await interaction.response.send_message(
            f"✅ TEAM UPDATED\nSlot {pos} cleared."
        )


client.tree.add_command(TeamCommands())


@client.tree.command(name="hunt", description="🌱 Spend coins and energy to roll animals")
@app_commands.describe(amount_coins="Coins to spend (divisible by 5)")
async def hunt(interaction: discord.Interaction, amount_coins: int):
    profile = store.load_profile(str(interaction.user.id))
    now_ts = now()
    if profile["cooldowns"]["hunt"] > now_ts:
        wait = format_cooldown(profile["cooldowns"]["hunt"] - now_ts)
        await interaction.response.send_message(
            f"⏳ Cooldown\nTry again in {wait}.", ephemeral=True
        )
        return
    if amount_coins <= 0 or amount_coins % 5 != 0:
        await interaction.response.send_message(
            "❌ Invalid amount\nUse a number divisible by 5 (e.g. 5, 25, 100).",
            ephemeral=True,
        )
        return

    rolls = amount_coins // 5
    if profile["coins"] < amount_coins:
        await interaction.response.send_message(
            "❌ Not enough coins", ephemeral=True
        )
        return
    if profile["energy"] < rolls:
        needed = rolls - profile["energy"]
        await interaction.response.send_message(
            f"❌ Not enough energy\nNeed {needed} more 🔋. Win battles to gain energy.",
            ephemeral=True,
        )
        return

    profile["coins"] -= amount_coins
    profile["energy"] -= rolls

    results: List[Tuple[Animal, str]] = []
    before_counts = {
        animal_id: total_owned_species(profile, animal_id) for animal_id in profile.get("zoo", {})
    }
    for _ in range(rolls):
        rarity = pick_rarity()
        pool = [a for a in ANIMALS.values() if a.rarity == rarity]
        animal = random.choice(pool)
        mutation = roll_mutation()
        add_animal(profile, animal.animal_id, mutation, 1)
        store.record_hatch(animal.animal_id)
        store.adjust_owned_count(animal.animal_id, 1)
        results.append((animal, mutation))

    profile["cooldowns"]["hunt"] = now_ts + 10
    store.save_profile(profile)

    grouped: Dict[str, Dict[str, int]] = {rarity: {} for rarity, _ in RARITY_ORDER}
    for animal, _mutation in results:
        grouped[animal.rarity][animal.animal_id] = grouped[animal.rarity].get(
            animal.animal_id, 0
        ) + 1

    lines = ["🌱 Hunt Results", "────────────────"]

    for rarity, symbol in RARITY_ORDER:
        animals = grouped[rarity]
        if not animals:
            continue
        entries = []
        for animal_id, count in sorted(animals.items()):
            animal = ANIMALS[animal_id]
            is_new = before_counts.get(animal_id, 0) == 0
            new_tag = " 🆕" if is_new else ""
            entries.append(f"{animal.emoji} {superscript_number(count)}{new_tag}")
        lines.append("")
        lines.append(f"{symbol} {rarity.capitalize()}")
        lines.append("  ".join(entries))

    lines.append("")
    lines.append("────────────────")
    lines.append(f"💰 Coins spent: {amount_coins}")
    lines.append(f"🔋 Energy used: {rolls}")

    await interaction.response.send_message("\n".join(lines))


class SellConfirmView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=15)
        self.user_id = user_id
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("You cannot respond to this.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Yes ✅", style=discord.ButtonStyle.success, emoji="🟢")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel ❌", style=discord.ButtonStyle.danger, emoji="🔴")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmed = False
        await interaction.response.defer()
        self.stop()


@client.tree.command(name="sell", description="💰 Sell animals for coins (reserves protected)")
@app_commands.describe(
    mode="Sell a single animal or all animals of a rarity",
    target="Emoji/alias when selling an animal, or rarity name",
    amount="Number to sell or 'all'",
)
@app_commands.choices(
    mode=[
        app_commands.Choice(name="Animal", value="animal"),
        app_commands.Choice(name="Rarity", value="rarity"),
        app_commands.Choice(name="Food", value="food"),
    ]
)
async def sell(
    interaction: discord.Interaction, mode: app_commands.Choice[str], target: str, amount: str
):
    mode_value = mode.value if isinstance(mode, app_commands.Choice) else str(mode)
    amount_lower = amount.lower().strip()
    sell_all = amount_lower == "all"
    sell_count = None
    if not sell_all:
        if not amount_lower.isdigit() or int(amount_lower) <= 0:
            await interaction.response.send_message(
                "❌ Invalid amount\nUse a positive number or 'all'.", ephemeral=True
            )
            return
        sell_count = int(amount_lower)

    profile = store.load_profile(str(interaction.user.id))

    def finalize_sale(changes: List[Tuple[Animal, str, int]]) -> Tuple[int, int]:
        total_coins = 0
        total_sold = 0
        for animal_obj, mutation, qty in changes:
            removed = remove_animal(profile, animal_obj.animal_id, mutation, qty)
            if removed <= 0:
                continue
            total_coins += removed * RARITY_SELL_VALUE[animal_obj.rarity]
            total_sold += removed
            store.adjust_owned_count(animal_obj.animal_id, -removed)
            store.record_sale(animal_obj.animal_id, removed)
        profile["coins"] += total_coins
        store.save_profile(profile)
        return total_sold, total_coins

    def allocate_sale(animal_obj: Animal, qty: int) -> List[Tuple[str, int]]:
        remaining = qty
        allocations: List[Tuple[str, int]] = []
        for mutation in MUTATIONS:
            available = sellable_amount(profile, animal_obj.animal_id, mutation)
            if available <= 0:
                continue
            portion = min(available, remaining)
            if portion > 0:
                allocations.append((mutation, portion))
                remaining -= portion
            if remaining <= 0:
                break
        if remaining > 0:
            raise RuntimeError("Sale allocation failed due to insufficient inventory")
        return allocations

    def summarize_plan(changes: List[Tuple[Animal, str, int]]) -> List[Tuple[Animal, int]]:
        summary: Dict[str, int] = {}
        for animal_obj, _mutation, qty in changes:
            summary[animal_obj.animal_id] = summary.get(animal_obj.animal_id, 0) + qty
        return [(ANIMALS[animal_id], qty) for animal_id, qty in summary.items()]

    if mode_value == "food":
        food_obj = resolve_food(target)
        if not food_obj:
            await interaction.response.send_message("❌ Unknown food. Try an emoji or alias.", ephemeral=True)
            return
        equipped_foods = set(profile.get("equipped_foods", {}).values())
        if food_obj.food_id in equipped_foods:
            await interaction.response.send_message(
                "❌ Cannot sell equipped food. Replace it first.", ephemeral=True
            )
            return
        owned = profile["foods"].get(food_obj.food_id, 0)
        if owned <= 0:
            await interaction.response.send_message("❌ You don't own that food.", ephemeral=True)
            return
        sell_amount = owned if sell_all else sell_count or 0
        if sell_amount > owned:
            await interaction.response.send_message(
                f"❌ Cannot sell\nYou can sell up to {owned} of that food.", ephemeral=True
            )
            return
        depreciation = 1.0
        wins_used = 0
        if sell_amount > 0:
            wins_used = 0
        final_value = max(0.5, depreciation) * food_obj.cost * sell_amount * 0.5
        profile["foods"][food_obj.food_id] = max(0, owned - sell_amount)
        profile["coins"] += int(final_value)
        store.save_profile(profile)
        await interaction.response.send_message(
            f"✅ SOLD\n{food_obj.emoji} x{sell_amount}\nValue after use: {int(final_value)} coins",
        )
        return
    if mode_value == "animal":
        a = resolve_animal(target)
        if not a:
            await interaction.response.send_message(
                "❌ Unknown animal\nTry an emoji or alias.", ephemeral=True
            )
            return
        reserved = reserved_species_count(profile["team"], a.animal_id)
        if reserved > 0:
            await interaction.response.send_message(
                "❌ Cannot sell\nThat animal is currently in your team.\nRemove it from the team first.",
                ephemeral=True,
            )
            return
        owned = total_owned_species(profile, a.animal_id)
        if owned <= 0:
            await interaction.response.send_message(
                "❌ Cannot sell\nYou don't own that animal.", ephemeral=True
            )
            return
        sell_amount = owned if sell_all else sell_count or 0
        available_amount = sellable_species_amount(profile, a.animal_id)
        if sell_amount > available_amount:
            await interaction.response.send_message(
                f"❌ Cannot sell\nYou can sell up to {available_amount} of that animal (team animals are excluded).",
                ephemeral=True,
            )
            return

        allocations = allocate_sale(a, sell_amount)
        plan = [(a, mutation, qty) for mutation, qty in allocations]
        needs_confirm = a.rarity in {"EPIC", "LEGENDARY", "SPECIAL", "HIDDEN"}

    else:
        rarity_key = target.strip().upper()
        if rarity_key not in RARITY_SELL_VALUE:
            await interaction.response.send_message(
                "❌ Invalid rarity\nUse common, uncommon, rare, epic, legendary, special, or hidden.",
                ephemeral=True,
            )
            return
        plan: List[Tuple[Animal, str, int]] = []
        for animal_obj in ANIMALS.values():
            if animal_obj.rarity != rarity_key:
                continue
            available_total = sellable_species_amount(profile, animal_obj.animal_id)
            if available_total <= 0:
                continue
            qty = available_total if sell_all else min(available_total, sell_count or 0)
            if qty > 0:
                for mutation, portion in allocate_sale(animal_obj, qty):
                    plan.append((animal_obj, mutation, portion))
        if not plan:
            await interaction.response.send_message(
                "❌ Cannot sell\nNo animals of that rarity are available (team animals are excluded).",
                ephemeral=True,
            )
            return
        needs_confirm = True

    if needs_confirm:
        embed = discord.Embed(title="⚠️ Confirm Sale", description="You are about to sell the following:")
        summary = summarize_plan(plan)
        embed.add_field(
            name="Items",
            value="\n".join(f"{animal.emoji} x{qty}" for animal, qty in summary),
            inline=False,
        )
        view = SellConfirmView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()
        await view.wait()
        if not view.confirmed:
            await message.edit(content="Sale cancelled.", embed=None, view=None)
            return
        total_sold, total_coins = finalize_sale(plan)
        await message.edit(
            content=f"✅ SOLD\nItems: {total_sold}\n💰 Coins: +{total_coins}",
            embed=None,
            view=None,
        )
        return

    total_sold, total_coins = finalize_sale(plan)
    await interaction.response.send_message(
        f"✅ SOLD\n{plan[0][0].emoji} x{total_sold}\n💰 Coins: +{total_coins}"
    )


@client.tree.command(name="fuse", description="⚒️ Fuse four animals into a higher mutation")
@app_commands.describe(
    animal="Emoji or alias of the animal to fuse",
    mutation="Mutation tier (none, golden, diamond, emerald)",
)
async def fuse(interaction: discord.Interaction, animal: str, mutation: str):
    a = resolve_animal(animal)
    if not a:
        await interaction.response.send_message(
            "❌ Unknown animal\nTry an emoji or alias.", ephemeral=True
        )
        return

    try:
        mutation_key = normalize_mutation_key(mutation)
    except ValueError:
        await interaction.response.send_message(
            "❌ Invalid mutation\nUse none, golden, diamond, emerald, or rainbow.",
            ephemeral=True,
        )
        return

    if mutation_key == "rainbow":
        await interaction.response.send_message(
            "❌ Rainbow animals cannot be fused further.", ephemeral=True
        )
        return

    profile = store.load_profile(str(interaction.user.id))
    available = sellable_amount(profile, a.animal_id, mutation_key)
    if available < 4:
        await interaction.response.send_message(
            "❌ Not enough to fuse\n"
            f"Need 4 of the same mutation. Available after team reservations: {available}.",
            ephemeral=True,
        )
        return

    removed = remove_animal(profile, a.animal_id, mutation_key, 4)
    if removed < 4:
        await interaction.response.send_message(
            "❌ Fusion failed\nInventory changed before fusion could complete.",
            ephemeral=True,
        )
        return

    result_mutation, result_qty = roll_fusion_result(mutation_key)
    add_animal(profile, a.animal_id, result_mutation, result_qty)

    owned_delta = result_qty - removed
    store.adjust_owned_count(a.animal_id, owned_delta)
    store.save_profile(profile)

    remaining_consumed = get_owned_count(profile, a.animal_id, mutation_key)
    remaining_result = get_owned_count(profile, a.animal_id, result_mutation)

    inventory_lines = [f"{format_mutation_label(mutation_key)}: x{remaining_consumed}"]
    if result_mutation != mutation_key:
        inventory_lines.append(
            f"{format_mutation_label(result_mutation)}: x{remaining_result}"
        )
    else:
        inventory_lines[0] = f"{format_mutation_label(result_mutation)}: x{remaining_result}"

    embed = discord.Embed(title="⚒️ Fusion Complete", color=0xF1C40F)
    embed.add_field(
        name="Consumed",
        value=(
            f"{a.emoji} {a.animal_id} x4 "
            f"({format_mutation_label(mutation_key)})"
        ),
        inline=False,
    )
    embed.add_field(
        name="Result",
        value=(
            f"{a.emoji} {a.animal_id} x{result_qty} "
            f"({format_mutation_label(result_mutation)})"
        ),
        inline=False,
    )
    embed.add_field(name="Inventory", value="\n".join(inventory_lines), inline=False)
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="battle", description="⚔️ Battle an enemy bot for rewards")
async def battle(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        profile = store.load_profile(str(interaction.user.id))
        now_ts = now()
        if profile["cooldowns"]["battle"] > now_ts:
            wait = format_cooldown(profile["cooldowns"]["battle"] - now_ts)
            await interaction.edit_original_response(content=f"⏳ Cooldown\nTry again in {wait}.")
            return
        if not all(profile["team"].get(f"slot{i}") for i in range(1, 4)):
            await interaction.edit_original_response(
                content="❌ Team incomplete\nSet slot 1 (TANK), slot 2 (ATTACK), slot 3 (SUPPORT)."
            )
            return

        player_animals: Dict[str, Animal] = {}
        player_mutations: Dict[str, str] = {}
        for i in range(1, 4):
            slot = f"slot{i}"
            slot_value = profile["team"].get(slot)
            if not isinstance(slot_value, dict) or not slot_value.get("animal_id"):
                await interaction.edit_original_response(
                    content="❌ Team incomplete\nSet slot 1 (TANK), slot 2 (ATTACK), slot 3 (SUPPORT)."
                )
                return
            player_animals[slot] = ANIMALS[slot_value["animal_id"]]
            try:
                player_mutations[slot] = normalize_mutation_key(slot_value.get("mutation", "none"))
            except ValueError:
                player_mutations[slot] = "none"
        player_foods: Dict[str, Optional[Food]] = {}
        for i in range(1, 4):
            slot = f"slot{i}"
            food_id = profile.get("equipped_foods", {}).get(slot)
            player_foods[slot] = FOODS.get(food_id) if food_id else None

        avg_index = round(
            sum(a.rarity_index for a in player_animals.values()) / 3
        )
        allowed = set()
        for idx in (avg_index - 1, avg_index, avg_index + 1):
            if 0 <= idx <= 6:
                allowed.add(idx)
        allowed_indices = sorted(allowed)

        player_final_power = 0.0
        for slot, animal in player_animals.items():
            mutation_multiplier = mutation_multiplier_value(player_mutations.get(slot, "none"))
            player_final_power += effective_power(animal, player_foods.get(slot), mutation_multiplier)

        target_min = player_final_power * 0.8
        target_max = player_final_power * 1.3
        last_signature = profile.get("last_enemy_signature")

        best_candidate: Optional[Tuple[Dict[str, Animal], Dict[str, Optional[Food]], Dict[str, str], float, str]] = None
        best_delta = float("inf")
        best_in_range: Optional[Tuple[Dict[str, Animal], Dict[str, Optional[Food]], Dict[str, str], float, str]] = None
        best_in_range_not_same: Optional[
            Tuple[Dict[str, Animal], Dict[str, Optional[Food]], Dict[str, str], float, str]
        ] = None

        for _attempt in range(300):
            enemy_animals = {
                "slot1": random_animal_by_rarity_and_role(allowed_indices, "TANK"),
                "slot2": random_animal_by_rarity_and_role(allowed_indices, "ATTACK"),
                "slot3": random_animal_by_rarity_and_role(allowed_indices, "SUPPORT"),
            }
            enemy_foods = {slot: random_enemy_food(animal) for slot, animal in enemy_animals.items()}
            enemy_mutations = {slot: random_enemy_mutation() for slot in enemy_animals}
            enemy_power = calculate_team_power(enemy_animals, enemy_foods, enemy_mutations)
            signature = enemy_signature(enemy_animals, enemy_mutations)

            candidate = (enemy_animals, enemy_foods, enemy_mutations, enemy_power, signature)
            delta = 0.0
            if enemy_power < target_min:
                delta = target_min - enemy_power
            elif enemy_power > target_max:
                delta = enemy_power - target_max

            if target_min <= enemy_power <= target_max:
                if signature != last_signature:
                    best_in_range_not_same = candidate
                    break
                if not best_in_range:
                    best_in_range = candidate
            if delta < best_delta:
                best_delta = delta
                best_candidate = candidate

        final_choice = best_in_range_not_same or best_in_range or best_candidate
        if not final_choice:
            await interaction.edit_original_response(
                content="❌ Battle setup failed. Please try again."
            )
            return
        chosen_animals, chosen_foods, chosen_mutations, _, _ = final_choice
        enemy_final_power = adjust_enemy_team(
            chosen_animals,
            chosen_foods,
            chosen_mutations,
            allowed_indices,
            target_min,
            target_max,
        )
        profile["last_enemy_signature"] = enemy_signature(chosen_animals, chosen_mutations)

        enemy_animals = chosen_animals
        enemy_foods = chosen_foods
        enemy_mutations = chosen_mutations

        enemy_final_power = calculate_team_power(enemy_animals, enemy_foods, enemy_mutations)
        if enemy_final_power < target_min or enemy_final_power > target_max:
            enemy_final_power = adjust_enemy_team(
                enemy_animals,
                enemy_foods,
                enemy_mutations,
                allowed_indices,
                target_min,
                target_max,
            )
        enemy_final_power = calculate_team_power(enemy_animals, enemy_foods, enemy_mutations)

        player_hp = {}
        enemy_hp = {}
        player_stats: Dict[str, Tuple[int, int, int]] = {}
        enemy_stats: Dict[str, Tuple[int, int, int]] = {}
        for slot, animal in player_animals.items():
            hp, atk, defense = apply_food(animal, player_foods.get(slot))
            player_stats[slot] = (hp, atk, defense)
            player_hp[slot] = hp
        for slot, animal in enemy_animals.items():
            hp, atk, defense = apply_food(animal, enemy_foods.get(slot))
            enemy_stats[slot] = (hp, atk, defense)
            enemy_hp[slot] = hp

        def first_alive(hp_map: Dict[str, int]) -> Optional[str]:
            for i in range(1, 4):
                slot = f"slot{i}"
                if hp_map[slot] > 0:
                    return slot
            return None

        def attack_phase(attacker_hp: Dict[str, int], attacker_stats: Dict[str, Tuple[int, int, int]], defender_hp: Dict[str, int], defender_stats: Dict[str, Tuple[int, int, int]]):
            for i in range(1, 4):
                slot = f"slot{i}"
                if attacker_hp.get(slot, 0) <= 0:
                    continue
                target_slot = first_alive(defender_hp)
                if not target_slot:
                    break
                def_value = sum(defender_stats[s][2] for s, hp in defender_hp.items() if hp > 0)
                dmg = max(1, attacker_stats[slot][1] - def_value)
                defender_hp[target_slot] = max(0, defender_hp[target_slot] - dmg)

        rounds = 0
        while first_alive(player_hp) and first_alive(enemy_hp) and rounds < 100:
            rounds += 1
            attack_phase(player_hp, player_stats, enemy_hp, enemy_stats)
            if not first_alive(enemy_hp):
                break
            attack_phase(enemy_hp, enemy_stats, player_hp, player_stats)

        player_alive = first_alive(player_hp) is not None
        enemy_alive = first_alive(enemy_hp) is not None
        cap_reached = rounds >= 100 and player_alive and enemy_alive
        if cap_reached:
            player_hp_total = sum(max(0, hp) for hp in player_hp.values())
            enemy_hp_total = sum(max(0, hp) for hp in enemy_hp.values())
            player_win = player_hp_total > enemy_hp_total
        else:
            player_win = player_alive and not enemy_alive

        enemy_final_power = calculate_team_power(enemy_animals, enemy_foods, enemy_mutations)
        enemy_multiplier = enemy_final_power / player_final_power if player_final_power > 0 else 1.0
        energy_gain = 1 if player_win else 0
        coin_gain = coins_reward(enemy_multiplier) if player_win else 0

        profile["energy"] += energy_gain
        profile["coins"] += coin_gain
        profile["cooldowns"]["battle"] = now_ts + 10
        if player_win:
            profile["battles_won"] = profile.get("battles_won", 0) + 1
            for slot, food_id in profile.get("equipped_foods", {}).items():
                if food_id:
                    profile["equipped_food_wins"][slot] = profile["equipped_food_wins"].get(slot, 0) + 1
        store.save_profile(profile)
        embed_color = 0x2ECC71 if player_win else 0xE74C3C
        banner = (
            "<:1636happypepe:1010165936646520973> YOU WON! <:1636happypepe:1010165936646520973>"
            if player_win
            else "<:cry:1416688020618215484> YOU LOST! <:cry:1416688020618215484>"
        )

        def format_line(
            role_emoji: str,
            animal_obj: Animal,
            mutation_key: str,
            food_obj: Optional[Food],
            current_hp: int,
            max_hp: int,
        ) -> str:
            mutation_emoji = MUTATION_META.get(mutation_key, MUTATION_META["none"]).get("emoji", "")
            pieces = [role_emoji, animal_obj.emoji, animal_obj.animal_id]
            if mutation_emoji:
                pieces.append(mutation_emoji)
            if food_obj:
                pieces.append(food_obj.emoji)
            header = " ".join(pieces)
            return f"{header}\nHP: {current_hp}/{max_hp}"

        enemy_lines = []
        for i in range(1, 4):
            slot = f"slot{i}"
            enemy_lines.append(
                format_line(
                    ROLE_EMOJI[enemy_animals[slot].role],
                    enemy_animals[slot],
                    enemy_mutations.get(slot, "none"),
                    enemy_foods.get(slot),
                    enemy_hp[slot],
                    enemy_stats[slot][0],
                )
            )

        player_lines = []
        for i in range(1, 4):
            slot = f"slot{i}"
            player_lines.append(
                format_line(
                    ROLE_EMOJI[player_animals[slot].role],
                    player_animals[slot],
                    player_mutations.get(slot, "none"),
                    player_foods.get(slot),
                    player_hp[slot],
                    player_stats[slot][0],
                )
            )

        embed = discord.Embed(title=banner, color=embed_color)
        embed.add_field(name="Enemy Team", value="\n\n".join(enemy_lines), inline=False)
        embed.add_field(name="Your Team", value="\n\n".join(player_lines), inline=False)
        embed.add_field(
            name="Rewards",
            value=f"💰 Coins: +{coin_gain}\n🔋 Energy: +{energy_gain}",
            inline=False,
        )

        await interaction.edit_original_response(content=None, embed=embed)
    except Exception as exc:
        print(f"❌ Battle error: {exc}")
        await interaction.edit_original_response(
            content=(
                "❌ Battle Failed\n"
                "Something went wrong during the fight.\n"
                "Please try again."
            )
        )




@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    print("====== COMMAND DEBUG ======")
    for cmd in client.tree.get_commands():
        print("-", cmd.name)
    print("===========================")




if __name__ == "__main__":
    client.run(TOKEN)
