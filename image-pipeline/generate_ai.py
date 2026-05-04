"""
EveryMood AI image generator — OpenAI gpt-image-1.

Fills the photo-quality gaps that Pillow can't:
  - Lifestyle scenes (model with bottle in different settings)
  - Hair before/after photography
  - Ingredient close-ups (HA droplet on petal, coconut crack, Vitamin E capsule)
  - Surface/texture studies (silk, marble, water reflection)
  - Alternate product scenes (using real bottle as reference)

Pillow stays the source of truth for typographic infographics.
This is the photo-realism layer on top.

Usage:
    export OPENAI_API_KEY=sk-...
    cd image-pipeline
    python3 generate_ai.py            # generate all
    python3 generate_ai.py only=hair  # generate one prompt by key

Cost notes (verify against current OpenAI pricing):
    - gpt-image-1 standard 1024x1024  ≈ $0.04 / image
    - gpt-image-1 high     1024x1024  ≈ $0.17 / image
    - All 9 prompts at high quality   ≈ $1.50 total
"""
from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Install: pip install openai")
    sys.exit(1)

ROOT = Path(__file__).parent
OUT = ROOT / "out-ai"
OUT.mkdir(exist_ok=True)
SRC_IMG = (ROOT / ".." / "images").resolve()

# Brand context prepended to every prompt for consistency
BRAND = (
    "EveryMood Berry Obsessed body and hair mist. Bottle is a translucent "
    "red/coral cylinder with a pink mist-spray base, white 'everymood' "
    "wordmark visible. Aesthetic: Gen Z, vibrant, playful, mood-shifting, "
    "skincare-first fragrance. Brand palette: hot pink, coral red, "
    "bubblegum, cream. Photo style: editorial commercial beauty, "
    "soft natural light, shallow depth of field, no visible text overlays."
)

# Prompts — each one fills a real gap in the existing 38-asset gallery
PROMPTS = {
    "lifestyle-office": (
        "A young woman in her 20s at a sunlit modern office desk, mid-afternoon "
        "golden hour light through floor-to-ceiling windows, casually spritzing "
        "EveryMood Berry Obsessed mist on her wrist, a laptop and oat-milk "
        "latte beside her, neutral linen blazer, soft glow on skin, photographed "
        "in Phlur / Glossier editorial style. Square 1:1 composition. No text."
    ),
    "lifestyle-gym": (
        "A young woman in athletic wear in a brightly lit boutique gym, "
        "post-workout glow, spritzing EveryMood Berry Obsessed mist into her "
        "ponytail, ambient light pink wall behind her, candid editorial shot, "
        "shallow depth of field, professional beauty photography. Square 1:1."
    ),
    "lifestyle-beach": (
        "A young woman at a beach club at sunset, holding the EveryMood Berry "
        "Obsessed bottle, sun-kissed shoulders, breeze in hair, warm pink and "
        "coral sunset palette in background, polaroid-style softness, Sol de "
        "Janeiro x Phlur visual language. Square 1:1, no text."
    ),
    "hair-after": (
        "Editorial hair beauty shot — close-up of a young woman's flowing dark "
        "hair, glossy and smooth, individual strands defined, studio softbox "
        "lighting, pink seamless background, treatment-finished hair texture. "
        "Photo style of Olaplex / Kerastase commercial editorial. Square 1:1, "
        "no text."
    ),
    "hair-before": (
        "Editorial hair beauty shot — close-up of a young woman's hair showing "
        "frizz, dryness, split ends, dull texture, flat lighting, cream "
        "background, before-treatment look used in beauty advertising for "
        "comparison shots. No model face visible. Square 1:1, no text."
    ),
    "ingredient-ha-macro": (
        "Macro photography — clear hyaluronic acid serum droplet on a single "
        "fresh pink rose petal, water beads of light catching the surface, "
        "extreme close-up, cinematic depth of field, soft natural light, "
        "skincare commercial style. Square 1:1, no text or labels."
    ),
    "ingredient-coconut-macro": (
        "Macro photography — a fresh whole coconut split open revealing white "
        "flesh and dripping coconut milk, on a pink marble surface, soft "
        "tropical light, skincare ingredient editorial. Square 1:1, no text."
    ),
    "ingredient-vitamin-e-macro": (
        "Macro photography — a translucent amber Vitamin E gel capsule "
        "released onto a satin pink fabric surface, golden droplet detail, "
        "soft beauty lighting, ingredient hero shot for skincare brand. "
        "Square 1:1, no text."
    ),
    "product-on-marble": (
        "Product photography — translucent red coral pink mist bottle "
        "(EveryMood Berry Obsessed style) standing on white marble countertop "
        "with fresh strawberries scattered around, single soft window light "
        "from upper left, magazine editorial, beauty commercial style. "
        "Square 1:1, no text overlays."
    ),
}


def generate_one(client: OpenAI, key: str, prompt: str, quality: str = "high",
                 size: str = "1024x1024") -> Path:
    """Generate a single image, save to out-ai/{key}.png"""
    full_prompt = BRAND + " " + prompt
    out_path = OUT / f"AI-{key}.png"
    print(f"→ Generating {key} ({quality}, {size}) ...", flush=True)
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=full_prompt,
        size=size,
        quality=quality,
        n=1,
    )
    b64 = resp.data[0].b64_json
    out_path.write_bytes(base64.b64decode(b64))
    print(f"   ✓ {out_path.relative_to(ROOT)} ({out_path.stat().st_size // 1024} KB)")
    return out_path


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: set OPENAI_API_KEY first.")
        print("  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    client = OpenAI()

    # CLI: generate_ai.py only=lifestyle-office
    selected = None
    quality = "high"
    for arg in sys.argv[1:]:
        if arg.startswith("only="):
            selected = arg.split("=", 1)[1]
        elif arg.startswith("quality="):
            quality = arg.split("=", 1)[1]

    keys = [selected] if selected else list(PROMPTS.keys())
    if selected and selected not in PROMPTS:
        print(f"Unknown key: {selected}")
        print(f"Available: {', '.join(PROMPTS.keys())}")
        sys.exit(1)

    print(f"Generating {len(keys)} image(s) at quality={quality}")
    print(f"Estimated cost: ~${len(keys) * (0.17 if quality == 'high' else 0.04):.2f}")
    print()

    for k in keys:
        try:
            generate_one(client, k, PROMPTS[k], quality=quality)
        except Exception as e:
            print(f"   ✗ {k} failed: {e}")

    print(f"\nDone. {len(keys)} attempted. Output in {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
