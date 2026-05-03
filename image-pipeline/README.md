# EveryMood image pipeline

Pillow-based generator that produces conversion-page imagery in the visual roles
the proven DTC template uses, but with **EveryMood's actual brand identity** —
Bricolage Grotesque typography, indigo / coral / pink / cream palette, and real
product photography from the EveryMood public CDN.

## What this is, and what it isn't

- ✅ Original Pillow code that I authored. Every layout, every composition.
- ✅ Real EveryMood product photos as the anchor visual (downloaded from the
     public Shopify CDN — these are public marketing assets the brand publishes
     for distribution).
- ✅ Real EveryMood font (Bricolage Grotesque, downloaded from Google Fonts).
- ✅ Real EveryMood brand colors extracted from the Berry Obsessed bottle.
- ✅ Universal DTC visual patterns (stats infographic, color-block + headline,
     before/after frame, "loved by N" grid, comparison shot, mood swatch row) —
     used by thousands of brands, not specific to any one source.
- ❌ No competitor product photos pulled in.
- ❌ No competitor copy lifted verbatim.
- ❌ No layouts that pixel-match a specific competitor template.

## Run

```bash
cd image-pipeline
python3 generate.py
```

Outputs land in `out/`. Re-run any time copy or palette changes — it's idempotent.

## Output catalog

| File | Visual role | When to use on LP |
|---|---|---|
| `01-stats-infographic.jpg` | 3 stat % + product on indigo brand block | Replaces or augments the clinical card. Strongest in proof-stack flow above reviews. |
| `02-adapts-to-mood.jpg` | Color-block + headline + bullets + product hero | Below-fold "Why EveryMood" anchor image, or social ad creative. |
| `03-before-after-hair.jpg` | Two-up template with branded pill labels | "Real Results" → Hair Health column upgrade. Drop real customer photos into the placeholder boxes. |
| `04-before-after-skin.jpg` | Same template, "Day 1 / Day 14" labels | Skin Hydration column upgrade. |
| `05-loved-by-grid.jpg` | 2x2 before/after grid frame with "Loved by 50,000+" headline + indigo plus | Top-of-reviews-section banner. Drop 4 real customer pairs into placeholder slots. |
| `06-comparison-shot.jpg` | Real bottle in center, 4 crossed-out generic luxury silhouettes around it | "Why EveryMood" Why section anchor — pairs with the "Why pay $100+ for alcohol-based perfume?" headline. |
| `07-mood-swatches.jpg` | "One mist. Every mood." headline + 8 mood color circles with active "YOU'RE HERE" pin on Juicy | Brand storytelling section between Why and Reviews. Reinforces the "every mood" platform thesis. |

## Color palette (verified against real bottle)

```
INDIGO     #505EE2   Logo wordmark
INDIGO     #3B47B8   Hover/deep
CORAL      #E84A5F   Berry Obsessed bottle
CORAL DEEP #C73848
PINK       #FF6B9E   Bubblegum
PINK PALE  #FFC9DD
PINK BLUSH #FFE9F1
CREAM      #FFF7EE
INK        #1B0F1A
LIME       #BFFF00   Use sparingly (from brief)
```

## Bricolage Grotesque setup

`fonts/` contains Regular / Bold / ExtraBold weights from Google Fonts. The `font()`
helper in `generate.py` loads them by weight name. Italic isn't included by default
(Bricolage's italic was added in later versions); for italic display headlines we
use a different approach — large ExtraBold and let the weight carry the emphasis.

## Where the gaps still are

The before/after and "Loved by 50,000" frames have placeholder boxes saying
`[ DROP REAL CUSTOMER PHOTO HERE ]`. For these to ship, you need:

1. **Real hair before/after pairs** — frizzy/dry on left, smooth/shiny on right.
   Source options:
   - User-generated content from existing EveryMood customers (DM ask + $20 gift card)
   - Studio shoot with a hair model (~4 hours, ~$1500)
   - Stock photography with explicit "use rights" — careful with attribution
2. **Real skin hydration before/after** — Day 1 vs Day 14 close-ups.
   Same sourcing options.
3. **Real "Loved by 50,000+" customer testimonials** with selfie photos.
   - Best: ask 4 power customers (the ones leaving 5-star reviews) for
     before/after selfie pairs in exchange for a year-supply.

Until these arrive, the placeholder versions still ship a more conversion-strong
page than emoji-only cards.

## How to add a new template

1. Add a new function to `generate.py` following the pattern of the existing six.
2. Use the `font()` helper for typography (regular / bold / xbold).
3. Use the palette constants at the top of the file.
4. Use `load("filename.png")` to pull a real product photo as the anchor.
5. Save with `canvas.save(out_path, quality=92)`.
6. Wire into `__main__` block at the bottom.

Re-run `python3 generate.py` and commit the new template.

## Drop into the live LP

Generated images are 1080×1080 (or 1300×900 for the before/after frame). Drop
into `images/` and reference in HTML. Example:

```html
<!-- Use 06-comparison-shot in the Why section -->
<img src="/image-pipeline/out/06-comparison-shot.jpg"
     alt="Why pay $100+ for alcohol-based perfume?">
```

## Why generate, not scrape

A reasonable instinct is: "the proven template has perfect images, just pull
them and re-label." Three reasons not to:

1. **Trademark/copyright exposure.** Competitor product photography on your LP
   is a takedown notice waiting to happen.
2. **Brand integrity.** EveryMood's identity is hot pink / coral / Bricolage —
   not whatever the source brand uses. Pulling their imagery dilutes you.
3. **Asset durability.** When you launch a second product, the third, the
   fourth — you want a generator that produces brand-consistent imagery on
   demand, not a scrape pile that's frozen in time.

This pipeline runs in 2 seconds and generates 7 brand-consistent assets. Adding
the 8th, 9th, 10th template is a function copy-paste away.
