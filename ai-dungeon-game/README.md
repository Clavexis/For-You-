# AI Dungeon

A text RPG where the story is generated as you play. Claude narrates the dungeon dynamically — and it's **fully playable offline** with a built-in procedural narrator.

## Demo

```text
── Floor 4 ──
You descend into an eerie crypt with flickering torchlight. A Skeleton
springs from the shadows!

⚔ Combat: Skeleton!

  You:        ████████████████████ 120/120
  Skeleton:   ████████ 40
  [a]ttack  [s]pecial  [d]efend  [u]se item  [f]lee
  > a
  You hit the Skeleton for 16 damage.
  The Skeleton hits you for 8 damage.
  ...
You defeated the Skeleton!
  Looted 12 gold.
```

## Features

- **AI-generated narration** — Claude describes each room and encounter (set `ANTHROPIC_API_KEY`). Falls back to a procedural narrator with no key needed.
- **Three character classes** — Warrior, Mage, Rogue — each with unique stats and a special move.
- **Turn-based combat** — attack, class special, defend, use items, or flee.
- **Inventory, health, gold, XP & levelling** — grow stronger as you descend.
- **Persistent saves** — save and resume your run (JSON).
- **Reproducible dungeons** — `--seed` for the same run every time.
- **Coloured terminal UI** with health bars.

## Classes

| Class | HP | ATK | DEF | Special |
|-------|----|-----|-----|---------|
| Warrior | 120 | 18 | 8 | Power Strike (heavy damage) |
| Mage | 80 | 24 | 3 | Fireball (big hit, costs HP) |
| Rogue | 95 | 20 | 5 | Backstab (high crit chance) |

## Installation

Requires only **Python 3.8+** (no dependencies to play offline; `anthropic` is optional for AI narration).

### Linux
```bash
cd linux && ./install.sh
ai-dungeon
```

### macOS (Apple Silicon & Intel)
```bash
cd mac && ./install.sh
ai-dungeon --class mage
```

### Windows
```powershell
cd windows
python dungeon.py
```

## Usage

```bash
ai-dungeon                     # choose a class and play
ai-dungeon --class rogue       # start as a rogue
ai-dungeon --seed 42           # reproducible dungeon
ai-dungeon --load my_save.json # continue a saved game
```

In the dungeon: `e` to explore deeper, `u` to use a potion, `s` to save, `q` to quit. In combat: `a`/`s`/`d`/`u`/`f`.

Set `ANTHROPIC_API_KEY` for AI-written room descriptions; without it, the procedural narrator takes over.

## Tech stack

- **Python 3** standard library — game engine, combat, save/load
- Optional [`anthropic`](https://pypi.org/project/anthropic/) SDK (`claude-opus-4-8`) for narration

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
