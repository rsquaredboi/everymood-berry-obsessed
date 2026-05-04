"""
Composite the REAL Berry Obsessed bottle PNG onto AI-generated scene
backgrounds — guarantees brand-accurate product across all AI gallery shots.

Workflow:
  1. Gemini generates the SCENE (with explicit empty bottle slot, no AI bottle)
  2. This script pastes the real `berry-hero.png` (transparent PNG) into the
     designated slot
  3. Output overwrites the AI-* file in /images/

Usage:
    cd image-pipeline
    python3 composite_bottle.py            # composite all configured scenes
    python3 composite_bottle.py only=hair-after
"""
from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).parent
SRC_AI = ROOT / "out-ai"
SRC_IMG = (ROOT / ".." / "images").resolve()

BOTTLE_PNG = SRC_IMG / "berry-hero.png"

# (anchor_x_pct, anchor_y_pct, bottle_height_pct, rotation_deg, shadow)
# Coordinates are % of scene dimensions. Anchor is bottom-center of bottle.
# Tuned to match the "empty slot" each AI prompt asks for.
SLOTS = {
    # IRL band — surface-placed scenes get the real bottle pasted in.
    # The "model holding bottle" scenes are NOT here — they're regen'd with
    # ref=True so Gemini renders the bottle naturally in-hand. Those scenes
    # are copied straight from out-ai/ to images/ unchanged.
    "AI-compliment-brunch":          {"x": 0.50, "y": 0.86, "h": 0.32, "rot":  0, "shadow": True},
    "AI-bathroom-shelf":             {"x": 0.30, "y": 0.72, "h": 0.34, "rot":  0, "shadow": True},
    # Editorial gallery — surface placements only
    "AI-berry-juice-splash":         {"x": 0.50, "y": 0.72, "h": 0.55, "rot":  0, "shadow": False},
    "AI-berry-bedside-ritual":       {"x": 0.28, "y": 0.62, "h": 0.36, "rot": -3, "shadow": True},
    "AI-berry-vanity-getting-ready": {"x": 0.50, "y": 0.70, "h": 0.36, "rot":  0, "shadow": True},
    "AI-berry-poolside-club":        {"x": 0.50, "y": 0.58, "h": 0.32, "rot": -3, "shadow": True},
    "AI-berry-farmers-market":       {"x": 0.62, "y": 0.58, "h": 0.40, "rot": -5, "shadow": True},
}


def composite(scene_path: Path, slot: dict, out_path: Path):
    """Paste real bottle into AI scene at the configured slot."""
    scene = Image.open(scene_path).convert("RGBA")
    bottle = Image.open(BOTTLE_PNG).convert("RGBA")
    sw, sh = scene.size

    # Resize bottle to target height
    target_h = int(sh * slot["h"])
    target_w = int(bottle.width * target_h / bottle.height)
    bottle = bottle.resize((target_w, target_h), Image.LANCZOS)

    # Optional rotation (slight tilt for naturalism)
    if slot.get("rot"):
        bottle = bottle.rotate(slot["rot"], resample=Image.BICUBIC, expand=True)
        target_w, target_h = bottle.size

    # Build a soft contact shadow under the bottle base if requested
    if slot.get("shadow"):
        shadow_layer = Image.new("RGBA", scene.size, (0, 0, 0, 0))
        # Elliptical contact shadow at base width, ~15% of bottle height
        sw_shadow = int(target_w * 0.85)
        sh_shadow = max(8, int(target_h * 0.10))
        ellipse = Image.new("RGBA", (sw_shadow, sh_shadow), (0, 0, 0, 0))
        from PIL import ImageDraw
        ImageDraw.Draw(ellipse).ellipse((0, 0, sw_shadow, sh_shadow), fill=(10, 5, 15, 150))
        ellipse = ellipse.filter(ImageFilter.GaussianBlur(radius=10))
        anchor_x = int(sw * slot["x"])
        anchor_y = int(sh * slot["y"])
        sx = anchor_x - sw_shadow // 2 + 4
        sy = anchor_y - sh_shadow // 2 + 2
        shadow_layer.paste(ellipse, (sx, sy), ellipse)
        scene = Image.alpha_composite(scene, shadow_layer)

    # Paste bottle (anchor = bottom-center)
    anchor_x = int(sw * slot["x"])
    anchor_y = int(sh * slot["y"])
    px = anchor_x - target_w // 2
    py = anchor_y - target_h
    scene.paste(bottle, (px, py), bottle)

    scene.convert("RGB").save(out_path, quality=92)
    print(f"  ✓ images/{out_path.name}")


def main():
    selected = None
    for arg in sys.argv[1:]:
        if arg.startswith("only="):
            selected = arg.split("=", 1)[1]
            if not selected.startswith("AI-"):
                selected = "AI-" + selected
    keys = [selected] if selected else list(SLOTS.keys())
    if selected and selected not in SLOTS:
        print(f"Unknown key: {selected}")
        print(f"Available: {', '.join(SLOTS.keys())}")
        sys.exit(1)

    print(f"Compositing real bottle into {len(keys)} scene(s)...")
    for k in keys:
        scene_path = SRC_AI / f"{k}.png"
        if not scene_path.exists():
            print(f"  ✗ {k}: scene not found at {scene_path}")
            continue
        out_path = SRC_IMG / f"{k}.png"
        composite(scene_path, SLOTS[k], out_path)
    print(f"\nDone. Composites overwrote /images/{{AI-*}}.png — refresh LP to see.")


if __name__ == "__main__":
    main()
