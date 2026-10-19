"""Build an optimized looping GIF and static preview from rendered frames."""
from __future__ import annotations

from pathlib import Path
from PIL import Image


def save_gif(frames: list[Image.Image], gif: Path, poster: Path, ms: int = 120,
             palette_sources: tuple[Path, ...] = ()) -> None:
    if not frames:
        raise ValueError("No rendered frames")
    gif.parent.mkdir(parents=True, exist_ok=True)
    poster.parent.mkdir(parents=True, exist_ok=True)
    frames[min(16, len(frames)-1)].save(poster, optimize=True)
    # Palette shared by every frame prevents color flicker and helps GIF delta encoding.
    ref = frames[min(15, len(frames)-1)].quantize(colors=112, method=Image.Quantize.MEDIANCUT)
    # Reserve exact sprite colors: a large green background otherwise crowds
    # the character's small gray, white and gold details out of the palette.
    sprite_colors = []
    for path in palette_sources:
        with Image.open(path) as sprite:
            palette = sprite.getpalette()
            if palette is None:
                raise ValueError(f"Expected a palette-based sprite: {path}")
            for offset in range(0, len(palette), 3):
                color = tuple(palette[offset:offset + 3])
                if color not in sprite_colors:
                    sprite_colors.append(color)
    if len(sprite_colors) > 144:
        raise ValueError("Sprite colors leave too little room for the background palette")
    if sprite_colors:
        reserved = [channel for color in sprite_colors for channel in color]
        ref.putpalette((reserved + ref.getpalette())[:768])
    converted = [frame.quantize(palette=ref, dither=Image.Dither.NONE) for frame in frames]
    converted[0].save(gif, save_all=True, append_images=converted[1:],
                      duration=ms, loop=0, disposal=1, optimize=True)
