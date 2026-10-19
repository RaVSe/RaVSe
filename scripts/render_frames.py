"""Render the supplied animated RaVSe mage over the contribution calendar."""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
W, H = 1640, 540
COLS, ROWS = 53, 7
CELL, GAP = 25, 4
STEP = CELL + GAP
GRID_X, GRID_Y = 56, 190
GRID_WIDTH = (COLS - 1) * STEP + CELL
GRID_HEIGHT = (ROWS - 1) * STEP + CELL
CELL_COLORS = ((11, 34, 27), (22, 75, 42), (31, 111, 49), (45, 158, 65), (108, 223, 99))
BG = ROOT / "assets/castle-bg.png"
FLYING = ROOT / "assets/mage-flying.gif"
CASTING = ROOT / "assets/mage-cast-spell.gif"
PROJECTILE = ROOT / "assets/green-projectile.gif"
SPRITE_SCALE = 3
FRAME_MS = 120
CHARGE_FRAMES, ORB_FRAMES, REST_FRAMES = 16, 5, 8


@dataclass(frozen=True)
class FramePlan:
    shot: int
    phase: str
    tick: int
    x: float
    y: float
    target: tuple[int, int] | None


def pick_targets(levels: list[list[int]], shots: int) -> list[tuple[int, int]]:
    # Select up to N genuine active cells, spread across the calendar's width.
    active = [(x, y) for x in range(COLS) for y in range(ROWS) if levels[x][y] > 0]
    # Keep breathing room near the left/right edges when there are enough targets.
    inner = [pos for pos in active if 5 <= pos[0] <= 50]
    if len(inner) >= shots:
        active = inner
    if not active or shots < 1:
        return []
    count = min(shots, len(active))
    if count == 1:
        return [active[len(active) // 2]]
    indices = [round(i * (len(active) - 1) / (count - 1)) for i in range(count)]
    return [active[i] for i in indices]


def load_animation(path: Path, native_size: tuple[int, int]) -> tuple[list[Image.Image], list[int]]:
    """Decode composited GIF frames, including transparency and merged-frame timing."""
    frames, durations = [], []
    with Image.open(path) as animation:
        for frame in ImageSequence.Iterator(animation):
            frames.append(frame.convert("RGBA").resize(native_size, Image.Resampling.NEAREST))
            durations.append(frame.info.get("duration", FRAME_MS))
    return frames, durations


class MageAnimation:
    def __init__(self):
        self.flying, self.flight_durations = load_animation(FLYING, (32, 32))
        self.casting, _ = load_animation(CASTING, (68, 32))
        self.projectiles, _ = load_animation(PROJECTILE, (32, 16))

    def sprite(self, plan: FramePlan, frame_id: int) -> Image.Image:
        if plan.phase == "charge":
            # Supplied cast frames 0..15: raise both hands and charge one orb.
            sprite = self.casting[plan.tick]
        elif plan.phase in ("orb", "shatter"):
            # This extended-arm pose has its baked-in missile far outside the
            # body crop. Only draw_projectile positions a missile on the grid.
            sprite = self.casting[27].crop((0, 0, 32, 32))
        elif plan.phase == "rest":
            sprite = self.casting[28 + plan.tick].crop((0, 0, 32, 32))
        else:
            elapsed = frame_id * FRAME_MS % sum(self.flight_durations)
            for sprite, duration in zip(self.flying, self.flight_durations):
                if elapsed < duration:
                    break
                elapsed -= duration
        return sprite.resize((sprite.width * SPRITE_SCALE, sprite.height * SPRITE_SCALE),
                             Image.Resampling.NEAREST)


def initial_base() -> Image.Image:
    if not BG.exists():
        raise FileNotFoundError(f"Required background missing: {BG}")
    return Image.open(BG).convert("RGB")


def centers(cell: tuple[int, int]) -> tuple[int, int]:
    x, y = cell
    return GRID_X + x * STEP + CELL // 2, GRID_Y + y * STEP + CELL // 2


def frames_schedule(targets: list[tuple[int, int]]) -> list[FramePlan]:
    """Four-stage spell per active cell: fly, wind up, one orb, shatter.

    The mage never shoots without a selected contribution tile.
    """
    schedule = []
    old = (GRID_X - 12, GRID_Y + GRID_HEIGHT / 2 - 95)
    if not targets:
        return [FramePlan(-1, "idle", i, old[0], old[1] + sin(i * pi / 6) * 3, None)
                for i in range(24)]
    for index, cell in enumerate(targets):
        cx, cy = centers(cell)
        to_x, to_y = max(2, cx - 141), cy - 67
        # Slight displacement avoids a mage continuously obscuring its target.
        for i in range(6):
            a = (i + 1) / 6
            a = a * a * (3 - 2*a)
            x = old[0] + (to_x - old[0]) * a
            y = old[1] + (to_y - old[1]) * a - 8 * sin(pi*a)
            schedule.append(FramePlan(index, "fly", i, x, y, cell))
        for i in range(CHARGE_FRAMES):
            schedule.append(FramePlan(index, "charge", i, to_x, to_y, cell))
        for i in range(ORB_FRAMES):
            schedule.append(FramePlan(index, "orb", i, to_x, to_y, cell))
        for i in range(3):
            schedule.append(FramePlan(index, "shatter", i, to_x, to_y, cell))
        for i in range(REST_FRAMES):
            schedule.append(FramePlan(index, "rest", i, to_x, to_y, cell))
        old = (to_x, to_y)
    # One brief interlude in which the grid is restored before looping.
    for i in range(10):
        schedule.append(FramePlan(len(targets), "reset", i, old[0], old[1], None))
    return schedule


def draw_grid(image: Image.Image, levels: list[list[int]], targets: list[tuple[int, int]], plan: FramePlan):
    d = ImageDraw.Draw(image)
    destroyed = set(targets[:max(0, plan.shot)])
    if plan.phase in ("shatter", "rest", "reset") and plan.target is not None:
        destroyed.add(plan.target)
    if plan.phase == "reset":
        # Smoothly re-light a group of destroyed tiles each frame.
        keep = round(len(destroyed) * max(0, 1 - (plan.tick + 1) / 10))
        destroyed = set(targets[:keep])
    for col in range(COLS):
        x0 = GRID_X + col * STEP
        for row in range(ROWS):
            y0 = GRID_Y + row * STEP
            level = levels[col][row]
            color = (7, 24, 20) if (col, row) in destroyed else CELL_COLORS[level]
            # Dark outlines, bright 1-pixel upper rim: crisp, large GitHub grid.
            d.rectangle((x0-1, y0-1, x0+CELL, y0+CELL), fill=(5, 18, 17))
            d.rectangle((x0, y0, x0+CELL-1, y0+CELL-1), fill=color)
            if (col, row) not in destroyed and level >= 3:
                d.line((x0+2, y0+2, x0+CELL-5, y0+2), fill=(88, 215, 93), width=1)
            if (col, row) in destroyed:
                d.line((x0+4, y0+CELL-4, x0+CELL-7, y0+CELL-4), fill=(13, 62, 40), width=1)


def draw_mage(image: Image.Image, animation: MageAnimation, plan: FramePlan, frame_id: int):
    sprite = animation.sprite(plan, frame_id)
    image.paste(sprite, (round(plan.x), round(plan.y)), sprite)


def draw_projectile(image: Image.Image, animation: MageAnimation, plan: FramePlan):
    if plan.target is None or plan.phase not in ("orb", "shatter"):
        return
    cx, cy = centers(plan.target)
    d = ImageDraw.Draw(image)
    source_x = round(plan.x) + 32 * SPRITE_SCALE
    source_y = round(plan.y) + 19 * SPRITE_SCALE
    if plan.phase == "orb":
        # Use the supplied bolt, keeping its head on the hand-to-target path.
        progress = (plan.tick + 1) / ORB_FRAMES
        px = round(source_x + (cx - source_x) * progress)
        py = round(source_y + (cy - source_y) * progress - 12 * sin(pi * progress))
        index = 4 + plan.tick
        bolt = animation.projectiles[index]
        bolt = bolt.resize((32 * SPRITE_SCALE, 16 * SPRITE_SCALE), Image.Resampling.NEAREST)
        head_x = round(2 + index * 2.6) * SPRITE_SCALE
        image.paste(bolt, (px - head_x, py - 8 * SPRITE_SCALE), bolt)
    else:
        # One localized explosion, a shower of separated green pixel shards.
        blast = 8 + plan.tick*10
        d.rectangle((cx-8,cy-8,cx+8,cy+8), fill=(140,255,100) if plan.tick == 0 else (11,50,27))
        if plan.tick < 2:
            d.ellipse((cx-blast,cy-blast,cx+blast,cy+blast), outline=(121,247,80), width=3)
        for i in range(19):
            ang = 2*pi*i/19
            radius = blast*(0.35+0.5*((i*7)%9)/9)
            fx = int(cx+radius*cos(ang)); fy = int(cy+radius*sin(ang))
            s = 3+i%3
            d.rectangle((fx,fy,fx+s,fy+s), fill=(167,255,96) if i%4==0 else (41,149,59))


def render_frames(levels: list[list[int]], shots: int = 12):
    if len(levels) != COLS or any(len(column) != ROWS for column in levels):
        raise ValueError(f"Expected a {COLS}x{ROWS} contribution grid")
    scene = initial_base()
    mage = MageAnimation()
    targets = pick_targets(levels, shots)
    timeline = frames_schedule(targets)
    for i, plan in enumerate(timeline):
        frame = scene.copy()
        draw_grid(frame, levels, targets, plan)
        draw_mage(frame, mage, plan, i)
        draw_projectile(frame, mage, plan)
        yield frame
