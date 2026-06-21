#!/usr/bin/env python3
"""
AI Dungeon — a text RPG where the story is generated as you play.

  - Claude narrates rooms, enemies, and events dynamically (with an offline
    procedural narrator so the game is fully playable without an API key).
  - Persistent game state saved to a JSON file.
  - Inventory, health, gold, and a turn-based combat system.
  - Multiple character classes (Warrior, Mage, Rogue).
  - Coloured terminal UI.

Usage:
  dungeon.py                 # new game (or continue a save)
  dungeon.py --class mage
  dungeon.py --load save.json
  dungeon.py --seed 42       # reproducible dungeon

Built by clavexis — github.com/clavexis
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

DEFAULT_MODEL = "claude-opus-4-8"
SAVE_FILE = "dungeon_save.json"


class C:
    RESET = "\033[0m"; BOLD = "\033[1m"; DIM = "\033[2m"
    GREEN = "\033[32m"; CYAN = "\033[36m"; YELLOW = "\033[33m"; RED = "\033[31m"; MAG = "\033[35m"

    @classmethod
    def off(cls):
        for n in ("RESET", "BOLD", "DIM", "GREEN", "CYAN", "YELLOW", "RED", "MAG"):
            setattr(cls, n, "")


if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C.off()


CLASSES = {
    "warrior": {"hp": 120, "attack": 18, "defense": 8, "special": "Power Strike (heavy damage)"},
    "mage":    {"hp": 80,  "attack": 24, "defense": 3, "special": "Fireball (hits hard, costs HP)"},
    "rogue":   {"hp": 95,  "attack": 20, "defense": 5, "special": "Backstab (high crit chance)"},
}

ENEMIES = [
    ("Goblin", 30, 8), ("Skeleton", 40, 10), ("Giant Rat", 20, 6),
    ("Orc", 55, 14), ("Dark Cultist", 45, 16), ("Cave Troll", 80, 18),
]

ITEMS = {
    "Health Potion": {"type": "heal", "amount": 40},
    "Greater Potion": {"type": "heal", "amount": 80},
    "Iron Sword": {"type": "weapon", "attack": 6},
    "Steel Shield": {"type": "armor", "defense": 5},
    "Gold Coin Pouch": {"type": "gold", "amount": 25},
}

ROOM_THEMES = [
    "a damp stone chamber dripping with moisture",
    "a vast hall lined with crumbling pillars",
    "a narrow corridor choked with cobwebs",
    "an eerie crypt with flickering torchlight",
    "a flooded cavern echoing with distant sounds",
    "a treasure vault sealed for centuries",
    "a moss-covered ruin open to a starless sky",
]


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, cls="warrior", seed=None):
        base = CLASSES[cls]
        self.cls = cls
        self.max_hp = base["hp"]
        self.hp = base["hp"]
        self.attack = base["attack"]
        self.defense = base["defense"]
        self.special = base["special"]
        self.inventory = ["Health Potion", "Health Potion"]
        self.gold = 0
        self.level = 1
        self.xp = 0
        self.room = 1
        self.seed = seed if seed is not None else random.randint(0, 10**9)
        self.alive = True
        self.rng = random.Random(self.seed)

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k != "rng"}
        return d

    @classmethod
    def from_dict(cls, d):
        g = cls.__new__(cls)
        g.__dict__.update(d)
        g.rng = random.Random(d.get("seed", 0))
        # Advance the RNG to roughly match the room count (keeps saves stable).
        for _ in range(d.get("room", 1)):
            g.rng.random()
        return g

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.level * 50:
            self.xp -= self.level * 50
            self.level += 1
            self.max_hp += 15
            self.hp = self.max_hp
            self.attack += 3
            print(f"{C.YELLOW}✨ Level up! You are now level {self.level}.{C.RESET}")


def hp_bar(hp, max_hp, width=20):
    ratio = max(0, hp) / max_hp if max_hp else 0
    filled = int(ratio * width)
    color = C.GREEN if ratio > 0.5 else C.YELLOW if ratio > 0.25 else C.RED
    return f"{color}{'█'*filled}{'░'*(width-filled)}{C.RESET} {max(0,hp)}/{max_hp}"


# ---------------------------------------------------------------------------
# Narration — AI if available, else procedural.
# ---------------------------------------------------------------------------
def ai_narrate(prompt):
    try:
        import anthropic
    except ImportError:
        return None
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=DEFAULT_MODEL, max_tokens=200,
            system="You are a vivid, concise dungeon master. Describe the scene in "
                   "2-3 atmospheric sentences. Do not ask questions or list options.",
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if b.type == "text").strip()
    except Exception:  # noqa: BLE001 — fall back to procedural narration
        return None


def narrate_room(game, theme, has_enemy, enemy_name=None):
    prompt = (f"The hero (a {game.cls}) enters {theme} on dungeon floor {game.room}. "
              + (f"A {enemy_name} lurks here, ready to attack." if has_enemy
                 else "The room is quiet."))
    ai = ai_narrate(prompt)
    if ai:
        return ai
    # Offline procedural narration.
    desc = f"You enter {theme}."
    if has_enemy:
        desc += f" A {C.RED}{enemy_name}{C.RESET} springs from the shadows!"
    else:
        desc += " It is quiet — for now."
    return desc


# ---------------------------------------------------------------------------
# Combat
# ---------------------------------------------------------------------------
def combat(game, enemy_name, enemy_hp, enemy_atk):
    print(f"\n{C.RED}{C.BOLD}⚔ Combat: {enemy_name}!{C.RESET}")
    while enemy_hp > 0 and game.hp > 0:
        print(f"\n  You:        {hp_bar(game.hp, game.max_hp)}")
        print(f"  {enemy_name+':':<11} {C.RED}{'█'*max(0, enemy_hp//5)}{C.RESET} {max(0,enemy_hp)}")
        print(f"  {C.DIM}[a]ttack  [s]pecial  [d]efend  [u]se item  [f]lee{C.RESET}")
        choice = input("  > ").strip().lower()

        player_dmg = 0
        defending = False
        if choice in ("a", "attack"):
            player_dmg = game.attack + game.rng.randint(-3, 5)
        elif choice in ("s", "special"):
            if game.cls == "mage":
                player_dmg = game.attack * 2; game.hp -= 10
                print(f"  {C.MAG}You hurl a Fireball! (-10 HP to cast){C.RESET}")
            elif game.cls == "rogue":
                player_dmg = game.attack * (3 if game.rng.random() < 0.5 else 1)
                print(f"  {C.MAG}You attempt a Backstab!{C.RESET}")
            else:
                player_dmg = int(game.attack * 1.8)
                print(f"  {C.MAG}You unleash a Power Strike!{C.RESET}")
        elif choice in ("d", "defend"):
            defending = True
            print("  You raise your guard.")
        elif choice in ("u", "use"):
            use_item(game)
            continue
        elif choice in ("f", "flee"):
            if game.rng.random() < 0.5:
                print(f"  {C.YELLOW}You flee successfully!{C.RESET}")
                return "fled"
            print(f"  {C.RED}You failed to flee!{C.RESET}")
        else:
            print("  (Invalid action.)")
            continue

        enemy_hp -= player_dmg
        if player_dmg:
            print(f"  You hit the {enemy_name} for {C.GREEN}{player_dmg}{C.RESET} damage.")
        if enemy_hp <= 0:
            break

        # Enemy turn.
        raw = enemy_atk + game.rng.randint(-2, 4)
        dmg = max(1, raw - game.defense - (game.defense if defending else 0))
        game.hp -= dmg
        print(f"  The {enemy_name} hits you for {C.RED}{dmg}{C.RESET} damage.")

    if game.hp <= 0:
        game.alive = False
        return "died"
    print(f"\n{C.GREEN}You defeated the {enemy_name}!{C.RESET}")
    loot_gold = game.rng.randint(5, 25)
    game.gold += loot_gold
    game.gain_xp(enemy_atk * 2)
    print(f"  Looted {loot_gold} gold.")
    if game.rng.random() < 0.4:
        item = game.rng.choice(list(ITEMS.keys()))
        game.inventory.append(item)
        print(f"  Found: {C.CYAN}{item}{C.RESET}!")
    return "won"


def use_item(game):
    potions = [i for i in game.inventory if ITEMS.get(i, {}).get("type") == "heal"]
    if not potions:
        print("  No usable items.")
        return
    item = potions[0]
    heal = ITEMS[item]["amount"]
    game.hp = min(game.max_hp, game.hp + heal)
    game.inventory.remove(item)
    print(f"  {C.GREEN}Used {item}, restored {heal} HP.{C.RESET}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def explore(game):
    theme = game.rng.choice(ROOM_THEMES)
    has_enemy = game.rng.random() < 0.6
    enemy = game.rng.choice(ENEMIES) if has_enemy else None
    print(f"\n{C.CYAN}{C.BOLD}── Floor {game.room} ──{C.RESET}")
    print(narrate_room(game, theme, has_enemy, enemy[0] if enemy else None))

    if has_enemy:
        result = combat(game, enemy[0], enemy[1] + game.room * 3, enemy[2] + game.room)
        if result == "died":
            return
    else:
        if game.rng.random() < 0.5:
            item = game.rng.choice(list(ITEMS.keys()))
            game.inventory.append(item)
            print(f"  You find a {C.CYAN}{item}{C.RESET}.")
    game.room += 1


def print_status(game):
    print(f"\n{C.BOLD}{game.cls.title()}{C.RESET} "
          f"Lv {game.level}  HP {hp_bar(game.hp, game.max_hp)}  "
          f"Gold {C.YELLOW}{game.gold}{C.RESET}  Floor {game.room}")
    print(f"  Inventory: {', '.join(game.inventory) or '(empty)'}")
    print(f"  Special: {game.special}")


def save_game(game, path):
    Path(path).write_text(json.dumps(game.to_dict(), indent=2))
    print(f"{C.GREEN}Saved to {path}.{C.RESET}")


def main():
    ap = argparse.ArgumentParser(description="AI Dungeon — a text RPG.")
    ap.add_argument("--class", dest="cls", choices=list(CLASSES), help="Character class.")
    ap.add_argument("--load", metavar="FILE", help="Load a saved game.")
    ap.add_argument("--seed", type=int, help="Dungeon seed (reproducible).")
    ap.add_argument("--save-file", default=SAVE_FILE, help="Save file path.")
    args = ap.parse_args()

    if args.load and os.path.exists(args.load):
        game = Game.from_dict(json.loads(Path(args.load).read_text()))
        print(f"{C.GREEN}Loaded save — {game.cls.title()}, floor {game.room}.{C.RESET}")
    else:
        cls = args.cls
        if not cls:
            print(f"{C.BOLD}Choose your class:{C.RESET}")
            for name, s in CLASSES.items():
                print(f"  {name:<8} HP {s['hp']:<4} ATK {s['attack']:<3} DEF {s['defense']:<3} — {s['special']}")
            cls = input("Class: ").strip().lower()
            if cls not in CLASSES:
                cls = "warrior"
        game = Game(cls, seed=args.seed)
        print(f"\n{C.CYAN}You descend into the dungeon as a {cls}. Seed: {game.seed}{C.RESET}")

    while game.alive:
        print_status(game)
        print(f"{C.DIM}[e]xplore deeper  [u]se potion  [s]ave  [q]uit{C.RESET}")
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cmd in ("e", "explore", ""):
            explore(game)
        elif cmd in ("u", "use"):
            use_item(game)
        elif cmd in ("s", "save"):
            save_game(game, args.save_file)
        elif cmd in ("q", "quit"):
            break

    if not game.alive:
        print(f"\n{C.RED}{C.BOLD}💀 You have fallen on floor {game.room}. "
              f"Final level: {game.level}, gold: {game.gold}.{C.RESET}")
        print("Game over.")
    else:
        print("Until next time, adventurer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
