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
    # CRITICAL: No bottle, no product, no container in shot. Pills label cells.
    "hair-before": {
        "ref": False,
        "prompt": "Editorial beauty close-up of a young woman's hair showing "
                  "frizziness, dryness, split ends, dull texture, slightly "
                  "tangled. Soft cream background, flat studio lighting. "
                  "Used in beauty commercial as 'before treatment' shot. "
                  "HAIR ONLY — absolutely no bottle, no product, no container, "
                  "no mist, no spray, no logo, no packaging, no jar visible. "
                  "Just the model and her hair. Square 1:1.",
    },
    "hair-after": {
        "ref": False,
        "prompt": "Editorial beauty close-up of a young woman's flowing dark "
                  "hair, glossy and smooth, individual strands defined, "
                  "treatment-finished texture, single subtle pink streak detail. "
                  "Soft pink seamless background, studio softbox lighting. "
                  "Magazine commercial 'after' look. HAIR ONLY — absolutely no "
                  "bottle, no product, no container, no mist, no spray, no logo, "
                  "no packaging visible anywhere in frame. Just the model and "
                  "her hair. Square 1:1.",
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
    # CRITICAL: NO bottle. Real bottle gets composited via Pillow.
    "compliment-brunch": {
        "ref": False,
        "prompt": "A young woman in her mid-20s at a sunlit brunch table, "
                  "her friend leaning in close to ask 'what are you wearing?', "
                  "warm candid moment, both smiling. Cream linen tablecloth, "
                  "fresh pink peonies in a vase, two small espresso cups, a "
                  "single fresh strawberry on the table — leave a clear empty "
                  "spot in the center-front of the table. Golden afternoon "
                  "light. Phlur / Sol de Janeiro editorial style. Square 1:1. "
                  "NO bottle, NO product, NO container, NO logo anywhere.",
    },
    # Hand spritzing moment — AI generates a pink bottle being held;
    # real bottle composited on top.
    "hand-spritz": {
        "ref": True,
        "prompt": "Editorial beauty shot — close-up of a young woman's hand "
                  "in upper-right of frame visibly gripping a small pink "
                  "wellness mist bottle (cylindrical, ~10cm tall, white spray "
                  "cap on top), spraying fine pink mist droplets downward "
                  "toward her other open palm in lower-left of frame. Bottle "
                  "MUST be clearly visible and held firmly. Soft pink seamless "
                  "backdrop, magazine fragrance commercial style, shallow "
                  "depth of field. Square 1:1.",
    },
    # Bathroom shelf flatlay
    "bathroom-shelf": {
        "ref": False,
        "prompt": "Top-down flatlay of a millennial bathroom counter — "
                  "ceramic dish with gold tweezers, small succulent in a "
                  "terracotta pot, eyelet linen towel, a tinted lip balm "
                  "tube, a folded eye mask. White marble surface with soft "
                  "window light from above. Leave a clear empty space in "
                  "the LEFT-CENTER of the composition (large enough for a "
                  "tall mist bottle). Editorial flatlay style. Square 1:1. "
                  "NO bottle, NO mist, NO product, NO container, NO logo.",
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
    # Editorial scenes — no bottle in shot. Real bottle composited via Pillow.
    "berry-vogue-portrait": {
        "ref": True,
        "prompt": "High-fashion editorial portrait — young woman early 20s, "
                  "bold hot-pink eyeshadow, glossy lips, dewy luminous skin, "
                  "diamond-stud earrings, head tilted toward the right. Her "
                  "left hand is raised near her left cheek visibly gripping a "
                  "small pink wellness mist bottle (cylindrical, ~10cm tall, "
                  "white spray cap on top). Bottle must be clearly visible "
                  "and held firmly between thumb and fingers. Saturated "
                  "magenta backdrop. Single hard rim light from upper left. "
                  "Vogue Beauty cover energy. Square 1:1.",
    },
    "berry-juice-splash": {
        "ref": False,
        "prompt": "Cinematic macro frozen-motion shot — pink mist and "
                  "strawberry juice droplets exploding outward in a 360-degree "
                  "splash around the EMPTY CENTER of the frame, fresh "
                  "strawberry halves suspended mid-air, a few raspberries and "
                  "rose petals captured in flight. Deep magenta-to-cream "
                  "gradient backdrop. Dramatic studio strobe lighting. "
                  "Super-sharp 1/8000s shutter feel. Square 1:1. CRUCIAL: "
                  "leave the center of the splash COMPLETELY EMPTY — no "
                  "bottle, no product, no container in the center.",
    },
    "berry-bedside-ritual": {
        "ref": False,
        "prompt": "Editorial lifestyle still-life — crumpled raspberry-pink "
                  "silk pillowcase with a small ceramic espresso cup, an "
                  "open hardcover book face-down, a single fresh strawberry, "
                  "and a folded eye mask. Soft morning light from a window "
                  "above-left. Leave clear EMPTY space in the upper-left of "
                  "the pillowcase composition (about 30% of the frame). Cozy "
                  "intimate millennial bedroom feel. Square 1:1, shallow "
                  "depth of field. NO bottle, NO mist, NO product anywhere.",
    },
    "berry-vanity-getting-ready": {
        "ref": False,
        "prompt": "Top-down vanity flatlay shot — scattered going-out "
                  "essentials: rose-gold compact mirror open, pink lip gloss "
                  "tube uncapped, hoop earrings in a small dish, a fresh "
                  "strawberry, a small swatch of pink eyeshadow on a tissue, "
                  "a folded silk scrunchie. Pearl-pink marble counter. Warm "
                  "filament bulb light from above. Leave clear EMPTY space "
                  "in the CENTER of the composition (~25% of the frame). "
                  "Square 1:1. NO bottle, NO mist, NO product, NO container.",
    },
    "berry-poolside-club": {
        "ref": False,
        "prompt": "Lifestyle editorial — bright pink inflatable pool float "
                  "in a sun-drenched rooftop pool at golden hour, water "
                  "sparkles, fresh strawberries floating nearby, a hand "
                  "reaching out from the water just visible at the edge of "
                  "frame. Warm pink-orange sunset palette. Leave a clear "
                  "EMPTY area on the float surface (top center). Square 1:1. "
                  "NO bottle, NO mist, NO product, NO container.",
    },
    "berry-hair-toss-mist": {
        "ref": True,
        "prompt": "Cinematic frozen-motion beauty shot — young woman "
                  "mid-hair-toss with long dark glossy hair flying in an "
                  "arc, fine pink mist droplets visible suspended in the air. "
                  "Her right hand is raised at chest level visibly gripping "
                  "a small pink wellness mist bottle (cylindrical, ~10cm "
                  "tall, white spray cap on top), spray nozzle aimed up at "
                  "her hair. Bottle must be clearly visible. Backlit by "
                  "hot-pink studio light, deep magenta backdrop. Action "
                  "beauty commercial energy. Square 1:1.",
    },
    "berry-farmers-market": {
        "ref": False,
        "prompt": "Lifestyle editorial — flatlay of an open canvas tote bag "
                  "spilling fresh strawberries, raspberries, and pink "
                  "peonies. Soft natural overhead market light, warm wood "
                  "plank surface. Leave clear EMPTY space inside the tote, "
                  "right-center of the composition (~25% of frame), nestled "
                  "among the produce — a natural slot for a tall bottle. "
                  "Square 1:1. NO bottle, NO mist, NO product visible.",
    },
    "berry-pink-on-pink": {
        "ref": True,
        "prompt": "Hyper-saturated fashion editorial — young woman in a "
                  "bright fuchsia silk slip dress against a fuchsia "
                  "seamless backdrop, head tilted right. Her left hand is "
                  "raised in front of her chest visibly gripping a small "
                  "pink wellness mist bottle (cylindrical, ~10cm tall, white "
                  "spray cap on top). Bottle clearly visible, held firmly. "
                  "Pink shimmer eyeshadow, soft smile. Single key light "
                  "through pink gel filter. Bold pink-on-pink monochromatic "
                  "energy. Square 1:1.",
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
