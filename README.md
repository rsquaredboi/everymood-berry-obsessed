# EveryMood — Berry Obsessed landing page

Static landing page for [EveryMood](https://everymood.com)'s Berry Obsessed
Hydrating Body & Hair Mist (100mL). Hand-written HTML, CSS, vanilla JS, plus a
Pillow-based image generator that produces 38 conversion-ready brand assets.

## Stack

- HTML / CSS / vanilla JS (no framework)
- [Bricolage Grotesque](https://fonts.google.com/specimen/Bricolage+Grotesque) at weights 400 / 500 / 700
- Brand palette extracted from the real Berry Obsessed bottle:
  coral `#E84A5F`, pink `#FF6B9E`, cream `#FFF7EE`, indigo `#505EE2` (logo)
- Real product photography from EveryMood's public Shopify CDN

## Run locally

```bash
# Static server on port 8766
python3 -m http.server 8766
# → http://localhost:8766/index.html
```

## Image pipeline

```bash
cd image-pipeline
python3 generate.py
# Outputs 38 assets to image-pipeline/out/
# Then copy to ../images/ if you want them on the LP
```

The generator produces three series:

- **A-series (8)**: standalone composite infographics — stats panel,
  color-block headline, comparison shot, mood swatch row, before/after
  templates, "loved by N" grid, press strip
- **B-series (14)**: photo-overlay variations on real EveryMood gallery
  photos — stat callouts, claim badges, scent pyramid, ingredient annotations,
  headline overlays, offer badges
- **C-series (16)**: fragrance-specific conversion assets — dupe comparison,
  day-to-night timeline, 0% denatured alcohol stamp, switched-from cards,
  hair-safe demo, scent pyramid (standalone), ingredient hero trio,
  free-from panel, pricing ladder, compliment wall, Mother's Day frame,
  gift bundle, TSA badge

See [`image-pipeline/README.md`](image-pipeline/README.md) for asset catalog.

## Conversion architecture

Mirrors proven DTC funnel structure — universal patterns, not specific to any
single source page:

- Top countdown banner (24h, localStorage-persisted)
- Sticky header with mini Claim Offer
- Hero split: headline + product gallery | buy box
- Tabs (Benefits / Why EveryMood / How It Works)
- Bundle picker (1x / 2x / 3x) with badges
- Subscribe & Save 15% toggle
- 10-min reservation timer
- Tiered gift unlock (locked → unlocked at 2x and 3x)
- Real Results 3-column with lifestyle photos + stat callouts
- "Why 50,000+ Women" section + dupe comparison visual
- Clinical proof (137% moisture retention, bar chart)
- Dermatologist endorsement
- Scent Profile (notes pyramid)
- Value-ladder positioning
- Compliment wall band
- Reviewer cards with scene photos + tags
- Final CTA + 6-question FAQ accordion
- Sticky mobile bottom CTA
- Upsell modal on Claim Offer

## File layout

```
everymood-berry-obsessed/
├── index.html             — Hand-written, all on-page copy
├── assets/
│   ├── styles.css         — EveryMood design system
│   └── everymood.js       — Countdown, bundle, subscribe, FAQ, modal, gallery
├── images/
│   ├── berry-*.png        — Real product photos (EveryMood CDN)
│   ├── em-logo.svg        — Real EveryMood logo
│   ├── em-bg-*.png        — Background vectors
│   ├── 01-08*.jpg         — A-series generated assets
│   ├── B1-B14*.jpg        — B-series generated assets
│   ├── C1-C15*.jpg        — C-series generated assets
│   └── gallery-overview.jpg — 4×10 contact sheet of all 38 assets
└── image-pipeline/
    ├── generate.py        — Pillow generator (~1700 lines)
    ├── README.md          — Pipeline docs
    └── fonts/             — Bricolage Grotesque TTFs (400/500/700)
```

## Customize for a different scent in the EveryMood family

1. Edit `index.html` — replace "Berry Obsessed" / "Strawberry Cream" /
   "Juicy & Vibrant" with the new scent's name / profile / mood
2. Drop new bottle photos into `images/`
3. Update product photo references in `index.html` and the bundle thumbs
4. In `image-pipeline/generate.py`, update copy strings inside each function
   (or parameterize them) and re-run

## Notes

- Pricing in this build is `$22 / $18.50 / $15` per bottle, anchored against
  `$34`. Adjust in `index.html` and `assets/everymood.js` (`CONFIG.anchorPrice`)
  for live promo math.
- Checkout URL stub is `https://everymood.com/cart` — wire to your real
  Shopify cart endpoint before going live.
- Free shipping triggers on 2x and 3x bundles.
- Free Mystery Mini and Free Scent Guide unlock on 3x bundle.
