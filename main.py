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

ROLE_EMOJI = {
    "TANK": "🛡️",
    "ATTACK": "⚔️",
    "SUPPORT": "🧪",
}


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
            initial_content = {"version": 2, "users": {}, "global": {"hatch_counts": {}}}
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
        data.setdefault("global", {"hatch_counts": {}})
        global_data = data.setdefault("global", {})
        global_data.setdefault("hatch_counts", {})
        global_data.setdefault("owned_counts", {})
        global_data.setdefault("sold_counts", {})
        global_data["owned_counts"] = self._recalculate_owned_counts(data.get("users", {}))
        return data

    def _recalculate_owned_counts(self, users: Dict[str, Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for profile in users.values():
            zoo = profile.get("zoo", {})
            for animal_id, qty in zoo.items():
                counts[animal_id] = counts.get(animal_id, 0) + max(0, qty)
        return counts

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
        }

    def load_profile(self, user_id: str) -> Dict:
        if user_id not in self.data.get("users", {}):
            self.data["users"][user_id] = self._default_profile(user_id)
            self._write_data()
        profile = self.data["users"][user_id]
        profile.setdefault("cooldowns", {"hunt": 0.0, "battle": 0.0})
        profile.setdefault("team", {"slot1": None, "slot2": None, "slot3": None})
        profile.setdefault("zoo", {})
        profile.setdefault("last_enemy_signature", None)
        profile.setdefault("foods", {})
        profile.setdefault("equipped_foods", {"slot1": None, "slot2": None, "slot3": None})
        profile.setdefault("equipped_food_wins", {"slot1": 0, "slot2": 0, "slot3": 0})
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


def reserved_count(team: Dict[str, Optional[str]], animal_id: str) -> int:
    return sum(1 for slot in team.values() if slot == animal_id)


def sellable_amount(profile: Dict, animal_id: str) -> int:
    return profile["zoo"].get(animal_id, 0) - reserved_count(profile["team"], animal_id)


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


def enemy_signature(team: Dict[str, Animal]) -> str:
    return "|".join(team[f"slot{i}"].animal_id for i in range(1, 4))


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
        embed.add_field(
            name=f"Filter: {filter_titles[self.filter_mode]}",
            value="\n\n".join(blocks) if blocks else "No animals match this filter.",
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
            amount = profile["zoo"].get(animal.animal_id, 0)
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
            animal_id = profile["team"].get(slot_key)
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
        owned = profile["zoo"].get(a.animal_id, 0)
        reserved = reserved_count(profile["team"], a.animal_id)
        if owned <= 0 and reserved == 0:
            await interaction.response.send_message(
                "❌ You don't own that animal yet.", ephemeral=True
            )
            return

        profile["team"][f"slot{pos}"] = a.animal_id
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

    results: List[Animal] = []
    before_counts = dict(profile["zoo"])
    for _ in range(rolls):
        rarity = pick_rarity()
        pool = [a for a in ANIMALS.values() if a.rarity == rarity]
        animal = random.choice(pool)
        profile["zoo"][animal.animal_id] = profile["zoo"].get(animal.animal_id, 0) + 1
        store.record_hatch(animal.animal_id)
        store.adjust_owned_count(animal.animal_id, 1)
        results.append(animal)

    profile["cooldowns"]["hunt"] = now_ts + 10
    store.save_profile(profile)

    grouped: Dict[str, Dict[str, int]] = {rarity: {} for rarity, _ in RARITY_ORDER}
    for animal in results:
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

    def finalize_sale(changes: List[Tuple[Animal, int]]) -> Tuple[int, int]:
        total_coins = 0
        total_sold = 0
        for animal_obj, qty in changes:
            current_amount = profile["zoo"].get(animal_obj.animal_id, 0)
            profile["zoo"][animal_obj.animal_id] = max(0, current_amount - qty)
            total_coins += qty * RARITY_SELL_VALUE[animal_obj.rarity]
            total_sold += qty
            store.adjust_owned_count(animal_obj.animal_id, -qty)
            store.record_sale(animal_obj.animal_id, qty)
        profile["coins"] += total_coins
        store.save_profile(profile)
        return total_sold, total_coins

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
        reserved = reserved_count(profile["team"], a.animal_id)
        if reserved > 0:
            await interaction.response.send_message(
                "❌ Cannot sell\nThat animal is currently in your team.\nRemove it from the team first.",
                ephemeral=True,
            )
            return
        owned = profile["zoo"].get(a.animal_id, 0)
        if owned <= 0:
            await interaction.response.send_message(
                "❌ Cannot sell\nYou don't own that animal.", ephemeral=True
            )
            return
        sell_amount = owned if sell_all else sell_count or 0
        if sell_amount > owned:
            await interaction.response.send_message(
                f"❌ Cannot sell\nYou can sell up to {owned} of that animal.",
                ephemeral=True,
            )
            return

        plan = [(a, sell_amount)]
        needs_confirm = a.rarity in {"EPIC", "LEGENDARY", "SPECIAL", "HIDDEN"}

    else:
        rarity_key = target.strip().upper()
        if rarity_key not in RARITY_SELL_VALUE:
            await interaction.response.send_message(
                "❌ Invalid rarity\nUse common, uncommon, rare, epic, legendary, special, or hidden.",
                ephemeral=True,
            )
            return
        plan: List[Tuple[Animal, int]] = []
        for animal_obj in ANIMALS.values():
            if animal_obj.rarity != rarity_key:
                continue
            available = sellable_amount(profile, animal_obj.animal_id)
            if available <= 0:
                continue
            qty = available if sell_all else min(available, sell_count or 0)
            if qty > 0:
                plan.append((animal_obj, qty))
        if not plan:
            await interaction.response.send_message(
                "❌ Cannot sell\nNo animals of that rarity are available (team animals are excluded).",
                ephemeral=True,
            )
            return
        needs_confirm = True

    if needs_confirm:
        embed = discord.Embed(title="⚠️ Confirm Sale", description="You are about to sell the following:")
        embed.add_field(
            name="Items",
            value="\n".join(f"{animal.emoji} x{qty}" for animal, qty in plan),
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
        if not all(profile["team"][f"slot{i}"] for i in range(1, 4)):
            await interaction.edit_original_response(
                content="❌ Team incomplete\nSet slot 1 (TANK), slot 2 (ATTACK), slot 3 (SUPPORT)."
            )
            return

        player_animals: Dict[str, Animal] = {
            f"slot{i}": ANIMALS[profile["team"][f"slot{i}"]] for i in range(1, 4)
        }
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

        player_power = sum(power(a) + food_power(player_foods[f"slot{i}"]) for i, a in player_animals.items())
        enemy_multiplier = random.uniform(0.85, 1.3)
        target_power = player_power * enemy_multiplier

        best_team: Optional[Dict[str, Animal]] = None
        best_delta = float("inf")
        last_signature = profile.get("last_enemy_signature")

        for attempt in range(50):
            enemy_team = {
                "slot1": random_animal_by_rarity_and_role(allowed_indices, "TANK"),
                "slot2": random_animal_by_rarity_and_role(allowed_indices, "ATTACK"),
                "slot3": random_animal_by_rarity_and_role(allowed_indices, "SUPPORT"),
            }
            signature = enemy_signature(enemy_team)
            if signature == last_signature:
                continue
            pwr = sum(power(a) for a in enemy_team.values())
            delta = abs(pwr - target_power)
            if delta < best_delta:
                best_delta = delta
                best_team = enemy_team
            if abs(pwr - target_power) <= target_power * 0.07:
                best_team = enemy_team
                break

        if not best_team:
            best_team = {
                "slot1": random_animal_by_rarity_and_role(allowed_indices, "TANK"),
                "slot2": random_animal_by_rarity_and_role(allowed_indices, "ATTACK"),
                "slot3": random_animal_by_rarity_and_role(allowed_indices, "SUPPORT"),
            }

        enemy_animals = best_team
        profile["last_enemy_signature"] = enemy_signature(enemy_animals)

        player_hp = {}
        enemy_hp = {slot: animal.hp for slot, animal in enemy_animals.items()}
        player_stats: Dict[str, Tuple[int, int, int]] = {}
        for slot, animal in player_animals.items():
            hp, atk, defense = apply_food(animal, player_foods.get(slot))
            player_stats[slot] = (hp, atk, defense)
            player_hp[slot] = hp

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
            attack_phase(player_hp, player_stats, enemy_hp, {slot: (a.hp, a.atk, a.defense) for slot, a in enemy_animals.items()})
            if not first_alive(enemy_hp):
                break
            attack_phase(enemy_hp, {slot: (a.hp, a.atk, a.defense) for slot, a in enemy_animals.items()}, player_hp, player_stats)

        player_alive = first_alive(player_hp) is not None
        enemy_alive = first_alive(enemy_hp) is not None
        cap_reached = rounds >= 100 and player_alive and enemy_alive
        if cap_reached:
            player_hp_total = sum(max(0, hp) for hp in player_hp.values())
            enemy_hp_total = sum(max(0, hp) for hp in enemy_hp.values())
            player_win = player_hp_total > enemy_hp_total
        else:
            player_win = player_alive and not enemy_alive

        energy_gain = 1 if player_win else 0
        coin_gain = coins_reward(enemy_multiplier) if player_win else 0

        profile["energy"] += energy_gain
        profile["coins"] += coin_gain
        profile["cooldowns"]["battle"] = now_ts + 10
        if player_win:
            for slot, food_id in profile.get("equipped_foods", {}).items():
                if food_id:
                    profile["equipped_food_wins"][slot] = profile["equipped_food_wins"].get(slot, 0) + 1
        store.save_profile(profile)
        embed_color = 0x2ECC71 if player_win else 0xE74C3C
        embed = discord.Embed(
            title="Victory" if player_win else "Defeat",
            description="Battle complete. Review the summary below.",
            color=embed_color,
        )
        embed.add_field(
            name="Battle Overview",
            value=(
                f"Enemy strength adapted to your squad and food boosts.\n"
                f"Difficulty hint: {'Weaker Enemy' if enemy_multiplier < 0.95 else 'Balanced Fight' if enemy_multiplier < 1.12 else 'Tough Enemy'}"
            ),
            inline=False,
        )

        survivor_lines = []
        for i in range(1, 4):
            slot = f"slot{i}"
            pa = player_animals[slot]
            ea = enemy_animals[slot]
            p_food = player_foods.get(slot)
            p_hp_max = player_stats[slot][0]
            survivor_lines.append(
                f"{ROLE_EMOJI[pa.role]} {pa.emoji} {pa.animal_id} {p_food.emoji if p_food else ''}\n"
                f"You: {player_hp[slot]}/{p_hp_max} | Enemy: {enemy_hp[slot]}/{ea.hp}"
            )
        embed.add_field(name="Survivors", value="\n\n".join(survivor_lines), inline=False)

        embed.add_field(
            name="Rewards",
            value=f"💰 Coins: +{coin_gain}\n🔋 Energy: +{energy_gain}",
            inline=False,
        )
        embed.add_field(
            name="Difficulty Hint",
            value="Weaker Enemy" if enemy_multiplier < 0.95 else "Balanced Fight" if enemy_multiplier < 1.12 else "Tough Enemy",
            inline=False,
        )
        embed.set_footer(text="Tip: Equip foods to push your power higher before battling again.")

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
