"""
Use Gemini 2.5 Flash Image as an image-editing model to NATURALLY
integrate the real Berry Obsessed bottle photo into AI-generated scenes.

Why: Pillow composite is a flat paste — no lighting integration, no
realistic shadow, no surface contact, no atmospheric blending. Gemini
multi-image input takes the actual bottle PNG + the AI scene and
generates a photo-real merged image where the bottle picks up the
scene's light, casts proper shadow, and integrates with surrounding
objects.

Inputs per scene:
  - Scene PNG (from out-ai/, generated with no bottle)
  - berry-hero.png (the real product)
  - Positioning prompt describing WHERE the bottle goes

Output: images/AI-{scene}.png (overwrites Pillow composite)

Usage:
    cd image-pipeline
    python3 compose_with_gemini.py only=compliment-brunch
    python3 compose_with_gemini.py            # all configured scenes
"""
from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
SRC_AI = ROOT / "out-ai"
SRC_IMG = (ROOT / ".." / "images").resolve()
BOTTLE_PNG = SRC_IMG / "berry-hero.png"


def load_key() -> str:
    k = os.environ.get("GEMINI_API_KEY")
    if k:
        return k
    env_path = Path("/Users/rahul/Downloads/nancy-cs-agent/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: No GEMINI_API_KEY")


API_KEY = load_key()
MODEL = "gemini-2.5-flash-image"
ENDPOINT = (f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODEL}:generateContent?key={API_KEY}")
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# Per-scene placement instruction. The ACTUAL bottle photo is passed too.
PLACEMENTS = {
    "AI-compliment-brunch": (
        "Take the Berry Obsessed bottle from image 2 and place it naturally "
        "on the empty round plate in the lower-center of the brunch scene "
        "in image 1. The bottle should sit upright on the plate with realistic "
        "warm afternoon lighting matching the scene, casting a soft shadow on "
        "the plate. Bottle should be appropriately sized — about as tall as "
        "an espresso cup. Keep the rest of the scene unchanged."
    ),
    "AI-bathroom-shelf": (
        "Take the Berry Obsessed bottle from image 2 and place it naturally "
        "on the marble bathroom shelf in image 1, in the empty space on the "
        "left-center of the flatlay. View it from a slight overhead top-down "
        "angle to match the flatlay perspective. Bottle should be sized in "
        "scale with the eye mask and small succulent. Add realistic soft "
        "shadow on the marble. Keep all other items unchanged."
    ),
    "AI-berry-juice-splash": (
        "Take the Berry Obsessed bottle from image 2 and place it floating "
        "in the center of the strawberry juice splash in image 1. The bottle "
        "should be vertical and sized to fit naturally inside the splash ring. "
        "Add subtle pink juice droplets clinging to the bottle and reflective "
        "highlights matching the dramatic studio lighting."
    ),
    "AI-berry-bedside-ritual": (
        "Take the Berry Obsessed bottle from image 2 and place it lying on "
        "its side OR standing upright on the pink silk pillowcase in image 1, "
        "in the upper-left empty space of the composition. Sized in scale "
        "with the espresso cup. Soft morning light shadow on the silk."
    ),
    "AI-berry-vanity-getting-ready": (
        "Take the Berry Obsessed bottle from image 2 and place it standing "
        "upright on the pink marble vanity in image 1, in the empty center "
        "space among the compact mirror, lip gloss, and earrings. Top-down "
        "flatlay perspective. Sized similar to the lip gloss tube. Soft warm "
        "shadow on the marble."
    ),
    "AI-berry-poolside-club": (
        "Take the Berry Obsessed bottle from image 2 and place it standing "
        "upright on the pink inflatable strawberry pool float in image 1, "
        "in the empty top-center area of the float. Golden-hour sunset "
        "lighting with warm rim light on the bottle. Bottle reflected "
        "subtly in the water below."
    ),
    "AI-berry-farmers-market": (
        "Take the Berry Obsessed bottle from image 2 and place it nestled "
        "naturally inside the canvas tote bag in image 1, among the pink "
        "peonies and strawberries, in the right-center area of the tote. "
        "Top-down flatlay perspective. Bottle visible standing upright, "
        "surrounded by produce and flowers."
    ),
}


BRAND = (
    "EveryMood Berry Obsessed body and hair mist — the real product. "
    "Photorealistic editorial photography. Match the original scene's "
    "lighting, shadows, and atmosphere exactly. The bottle MUST look "
    "identical to the reference photo: clear glass body with pink-tinted "
    "liquid, white spray cap, cream label with red 'EveryMood' wordmark "
    "and 'Berry Obsessed' subline. Do NOT redesign the bottle, do NOT "
    "change any other element of the scene. Output should look like a "
    "professional commercial product shot. Square 1:1. NO text overlays, "
    "NO watermarks. "
)


def b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode()


def compose_one(scene_path: Path, placement: str) -> bytes:
    """Pass scene + bottle + placement prompt to Gemini. Return new image bytes."""
    parts = [
        {"text": BRAND + placement},
        {"inline_data": {"mime_type": "image/png", "data": b64(scene_path)}},
        {"inline_data": {"mime_type": "image/png", "data": b64(BOTTLE_PNG)}},
    ]
    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 0.7,
        },
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=180) as r:
        resp = json.loads(r.read())
    for c in resp.get("candidates", []):
        for p in c.get("content", {}).get("parts", []):
            if "inline_data" in p:
                return base64.b64decode(p["inline_data"]["data"])
            if "inlineData" in p:
                return base64.b64decode(p["inlineData"]["data"])
    raise RuntimeError(f"No image in response: {json.dumps(resp)[:500]}")


def main():
    selected = None
    for arg in sys.argv[1:]:
        if arg.startswith("only="):
            selected = arg.split("=", 1)[1]
            if not selected.startswith("AI-"):
                selected = "AI-" + selected
    keys = [selected] if selected else list(PLACEMENTS.keys())
    if selected and selected not in PLACEMENTS:
        print(f"Unknown: {selected}")
        print(f"Available: {', '.join(PLACEMENTS.keys())}")
        sys.exit(1)

    print(f"Composing real bottle into {len(keys)} scene(s) via Gemini...")
    for k in keys:
        scene_path = SRC_AI / f"{k}.png"
        out_path = SRC_IMG / f"{k}.png"
        if not scene_path.exists():
            print(f"  ✗ {k}: scene missing at {scene_path}")
            continue
        print(f"  → {k} ...", flush=True)
        try:
            img_bytes = compose_one(scene_path, PLACEMENTS[k])
            out_path.write_bytes(img_bytes)
            print(f"     ✓ images/{out_path.name} ({len(img_bytes)//1024} KB)")
        except Exception as e:
            print(f"     ✗ {e}")
        time.sleep(15)  # rate limit
    print("\nDone.")


if __name__ == "__main__":
    main()
