"""
EveryMood AI image generator — Gemini 2.5 Flash Image.

Fills photo-quality gaps with EveryMood-original imagery in the visual styles
the proven DTC funnel uses (hair before/after, skin glow B/A, compliment
moments, ingredient macros, lifestyle scenes, flatlays).

Per the MEMORY.md notes:
  - Model: gemini-2.5-flash-image (responseModalities ['TEXT','IMAGE'])
  - Reference-based: always upload bottle hero as base64 inline data
    alongside text prompt → locks character/product design
  - Rate limit: 15s between calls
  - SSL on macOS: disable verification

Loads GEMINI_API_KEY from ~/Downloads/nancy-cs-agent/.env if not in env.

Usage:
    cd image-pipeline
    python3 generate_gemini.py            # generate all
    python3 generate_gemini.py only=hair-after
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
OUT = ROOT / "out-ai"
OUT.mkdir(exist_ok=True)
SRC_IMG = (ROOT / ".." / "images").resolve()

# ─── Load GEMINI_API_KEY ───
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
    sys.exit("ERROR: No GEMINI_API_KEY in env or nancy-cs-agent/.env")


API_KEY = load_key()
MODEL = "gemini-2.5-flash-image"
ENDPOINT = (f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODEL}:generateContent?key={API_KEY}")

# SSL context for macOS quirk per MEMORY.md
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


# ─── Prompts ───
# Each prompt fills a specific gap that Pillow can't (photo-realistic
# scenes / textures / faces). Brand prompt prepended for consistency.

BRAND = (
    "EveryMood Berry Obsessed body and hair mist. Aesthetic: Gen Z, "
    "vibrant, playful, mood-shifting. Photo style: editorial commercial "
    "beauty, soft natural light, shallow depth of field, magazine-quality. "
    "Brand palette: hot pink, coral red, bubblegum, cream. NO text overlays, "
    "NO logos, NO watermarks. "
)

# Some prompts use the bottle reference, others don't
PROMPTS = {
    # Hair before/after — fills the C5 hair-safe demo placeholder slots
    "hair-before": {
        "ref": False,
        "prompt": "Editorial beauty close-up of a young woman's hair showing "
                  "frizziness, dryness, split ends, dull texture, slightly "
                  "tangled. Soft cream background, flat studio lighting. "
                  "Used in beauty commercial as 'before treatment' shot. "
                  "Hair only, face partially visible from below. Square 1:1.",
    },
    "hair-after": {
        "ref": False,
        "prompt": "Editorial beauty close-up of a young woman's flowing dark "
                  "hair, glossy and smooth, individual strands defined, "
                  "treatment-finished texture. Soft pink seamless background, "
                  "studio softbox lighting. Magazine commercial 'after' look. "
                  "Hair only, face partially visible from below. Square 1:1.",
    },
    # Skin glow before/after
    "skin-before": {
        "ref": False,
        "prompt": "Macro skin texture close-up, dry dehydrated cheek of a "
                  "young woman, slightly flaky, dull, before skincare. "
                  "Cream background, flat lighting. Beauty commercial "
                  "'before' shot. Square 1:1.",
    },
    "skin-after": {
        "ref": False,
        "prompt": "Macro skin texture close-up, glowing hydrated cheek of a "
                  "young woman, plump and dewy, healthy radiance. Soft pink "
                  "background, golden hour glow. Beauty commercial 'after'. "
                  "Square 1:1.",
    },
    # Compliment moment scene — for reviewer cards
    "compliment-brunch": {
        "ref": True,
        "prompt": "A young woman in her mid-20s at a sunlit brunch table, "
                  "her friend leaning in close to ask 'what are you wearing?', "
                  "warm candid moment, both smiling. Cream linen, fresh "
                  "flowers, latte cups, golden afternoon light. The bottle "
                  "shown in the reference is visible on the table. "
                  "Photographed in Phlur / Sol de Janeiro editorial style. "
                  "Square 1:1, no text.",
    },
    # Hand spritzing moment
    "hand-spritz": {
        "ref": True,
        "prompt": "Editorial beauty shot — close-up of a young woman's wrist "
                  "and hand, mid-spritz, fine mist droplets visible in soft "
                  "backlight, soft pink seamless background. The bottle shown "
                  "in the reference is in her other hand. Magazine fragrance "
                  "commercial style, shallow depth of field. Square 1:1.",
    },
    # Bathroom shelf flatlay
    "bathroom-shelf": {
        "ref": True,
        "prompt": "Top-down flatlay of a millennial bathroom counter — "
                  "the bottle shown in the reference (Berry Obsessed mist) "
                  "centered, surrounded by other minimalist beauty items: "
                  "ceramic dish, gold tweezers, small succulent, eyelet "
                  "linen towel, and a tinted lip balm. White marble surface, "
                  "soft window light from above. Editorial flatlay style. "
                  "Square 1:1, no text.",
    },
    # Ingredient macros (no reference needed)
    "ingredient-ha": {
        "ref": False,
        "prompt": "Macro photography — a single clear hyaluronic acid serum "
                  "droplet on a fresh pink rose petal, water beads catching "
                  "light, extreme close-up, cinematic depth of field, soft "
                  "natural light. Skincare brand commercial. Square 1:1, no text.",
    },
    "ingredient-coconut": {
        "ref": False,
        "prompt": "Macro photography — a fresh whole coconut split open "
                  "revealing white flesh and dripping coconut milk, on a "
                  "soft pink marble surface, soft tropical light, skincare "
                  "ingredient hero shot. Square 1:1, no text.",
    },
    "ingredient-vitamin-e": {
        "ref": False,
        "prompt": "Macro photography — a translucent amber Vitamin E gel "
                  "capsule released onto satin pink fabric surface, golden "
                  "droplet detail catching light, soft beauty lighting. "
                  "Skincare ingredient hero. Square 1:1, no text.",
    },

    # ──────────────────────────────────────────────────────
    # BERRY-CINEMATIC SET — magazine-cover energy
    # Editorial fashion, hyper-saturated, conversion ad creative
    # ──────────────────────────────────────────────────────
    "berry-vogue-portrait": {
        "ref": True,
        "prompt": "High-fashion editorial portrait — young woman early 20s, "
                  "bold hot-pink eyeshadow, glossy lips, dewy luminous skin, "
                  "diamond-stud earrings, holding the EveryMood Berry "
                  "Obsessed bottle from the reference image close to her "
                  "cheek. Saturated magenta backdrop, single hard rim light "
                  "from upper left, slight specular highlight on bottle. "
                  "Vogue Beauty cover energy. Hyper-real skin texture. "
                  "Square 1:1, no text overlays, no logos, no watermarks.",
    },
    "berry-juice-splash": {
        "ref": True,
        "prompt": "Cinematic macro frozen-motion shot — the EveryMood Berry "
                  "Obsessed bottle from reference centered, pink mist and "
                  "strawberry juice droplets exploding outward in 360 around "
                  "the bottle, fresh strawberry halves suspended mid-air, a "
                  "few raspberries and rose petals captured in flight. Deep "
                  "magenta-to-cream gradient backdrop, dramatic studio strobe "
                  "lighting, super-sharp 1/8000s shutter feel. Beauty product "
                  "campaign style. Square 1:1, no text.",
    },
    "berry-bedside-ritual": {
        "ref": True,
        "prompt": "Editorial lifestyle still-life — the bottle from reference "
                  "on a crumpled raspberry-pink silk pillowcase, beside a "
                  "small ceramic espresso cup, an open hardcover book "
                  "face-down, a single strawberry, soft morning light "
                  "streaming from a window above-left. Cozy intimate "
                  "millennial bedroom feel. Phlur / Glossier campaign "
                  "aesthetic. Square 1:1, shallow depth of field, no text.",
    },
    "berry-vanity-getting-ready": {
        "ref": True,
        "prompt": "Top-down vanity flatlay shot — the bottle from reference "
                  "centered among scattered going-out essentials: rose-gold "
                  "compact mirror open, pink lip gloss tube uncapped, hoop "
                  "earrings in a small dish, a fresh strawberry, a swatch "
                  "of pink eyeshadow on a tissue. Pearl-pink marble counter, "
                  "warm filament bulb light from above. 'Getting ready' "
                  "narrative. Square 1:1, no text.",
    },
    "berry-poolside-club": {
        "ref": True,
        "prompt": "Lifestyle editorial — the bottle from reference resting "
                  "on a bright pink inflatable pool float in a sun-drenched "
                  "rooftop pool at golden hour, water sparkles, fresh "
                  "strawberries floating nearby in the pool, a hand reaching "
                  "out from the water just visible at the edge of frame. "
                  "Warm pink-orange sunset palette. Sol de Janeiro x Phlur "
                  "summer campaign visual language. Square 1:1, no text.",
    },
    "berry-hair-toss-mist": {
        "ref": True,
        "prompt": "Cinematic frozen-motion beauty shot — young woman "
                  "mid-hair-toss with long dark glossy hair flying in an arc, "
                  "fine pink mist droplets visible from the bottle in the "
                  "reference (held in her other hand), backlit by a hot-pink "
                  "studio light, deep magenta backdrop. Action beauty "
                  "commercial energy, super-sharp shutter. Square 1:1, no "
                  "text.",
    },
    "berry-farmers-market": {
        "ref": True,
        "prompt": "Lifestyle editorial — flatlay of an open canvas tote bag "
                  "spilling fresh strawberries, raspberries, and pink "
                  "peonies, with the bottle from reference nestled among "
                  "the produce. Soft natural overhead market light, warm "
                  "wood plank surface. Farmer's market Saturday morning "
                  "feel. Magazine still-life style. Square 1:1, no text.",
    },
    "berry-pink-on-pink": {
        "ref": True,
        "prompt": "Hyper-saturated fashion editorial — young woman in a "
                  "bright fuchsia silk slip dress against a fuchsia "
                  "seamless backdrop, holding the bottle from reference "
                  "to her cheek with a soft smile, pink shimmer eyeshadow, "
                  "single key light bouncing through pink gel filter. "
                  "Bold pink-on-pink monochromatic energy. Fashion campaign "
                  "style. Square 1:1, no text overlays, no logos.",
    },
}


def encode_ref() -> str:
    """Encode the real Berry Obsessed bottle photo as base64 for reference."""
    ref_path = SRC_IMG / "berry-hero.png"
    return base64.b64encode(ref_path.read_bytes()).decode()


def call_gemini(prompt: str, use_ref: bool = False) -> bytes:
    """Call Gemini 2.5 Flash Image. Returns raw image bytes."""
    parts = [{"text": BRAND + " " + prompt}]
    if use_ref:
        parts.append({
            "inline_data": {
                "mime_type": "image/png",
                "data": encode_ref(),
            }
        })
    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "temperature": 1.0,
        },
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=120) as r:
        resp = json.loads(r.read())
    # Walk response structure for image data
    candidates = resp.get("candidates", [])
    for c in candidates:
        for p in c.get("content", {}).get("parts", []):
            if "inline_data" in p:
                return base64.b64decode(p["inline_data"]["data"])
            if "inlineData" in p:  # camelCase alt
                return base64.b64decode(p["inlineData"]["data"])
    raise RuntimeError(f"No image in response: {json.dumps(resp)[:500]}")


def generate_one(key: str, spec: dict) -> Path:
    out_path = OUT / f"AI-{key}.png"
    print(f"→ {key} (ref={spec['ref']}) ...", flush=True)
    img_bytes = call_gemini(spec["prompt"], use_ref=spec["ref"])
    out_path.write_bytes(img_bytes)
    print(f"   ✓ {out_path.relative_to(ROOT)} ({out_path.stat().st_size // 1024} KB)")
    return out_path


def main():
    selected = None
    for arg in sys.argv[1:]:
        if arg.startswith("only="):
            selected = arg.split("=", 1)[1]
    keys = [selected] if selected else list(PROMPTS.keys())
    if selected and selected not in PROMPTS:
        print(f"Unknown key. Available: {', '.join(PROMPTS.keys())}")
        sys.exit(1)
    print(f"Generating {len(keys)} via {MODEL}\n")
    for i, k in enumerate(keys):
        try:
            generate_one(k, PROMPTS[k])
        except Exception as e:
            print(f"   ✗ {k} failed: {e}")
        if i < len(keys) - 1:
            time.sleep(15)  # rate limit per MEMORY
    print(f"\nDone. Output → {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
