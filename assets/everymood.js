/**
 * EveryMood Berry Obsessed — landing page interactivity
 *
 * Mirrors the conversion architecture of the proven template:
 *  - 24h countdown (localStorage persistence, never 00:00:00:00)
 *  - Bundle selector (1x / 2x / 3x) with live total + freebies row on 3x
 *  - Subscribe & Save toggle (15% off)
 *  - 10-min reservation timer
 *  - Tab switcher (Benefits / Why EveryMood / How It Works)
 *  - FAQ accordion
 *  - Hero thumbnail strip
 *  - Claim Offer → upsell modal with timer
 *  - Sticky mobile CTA → same modal
 *  - Dynamic ship date "Mon, May 11"
 */
(() => {
  'use strict';

  const CONFIG = {
    countdownHours: 24,
    reservationMinutes: 10,
    subscribeDiscount: 0.15,
    anchorPrice: 34.00,
    checkoutUrl: 'https://everymood.com/cart',
    upsell: {
      name: 'Vanilla Soft Serve',
      tagline: 'Body & Hair Mist · 100mL',
      mood: 'Sweet & Flirty',
      img: 'images/vanilla-soft-serve.png',
      desc: 'Pairs perfectly with Berry Obsessed. Vanilla cream + soft musk for the cozier mood.',
      price: 22.00,
      original: 35.00,
      bullets: [
        'Same skincare-first formula (HA + Coconut + Vit E)',
        'Sweet & Flirty mood — vanilla cream + soft musk',
        'Layer with Berry Obsessed for a custom scent'
      ]
    }
  };

  const state = window.__em = {
    bundleIdx: 2,
    count: 3,
    each: 15.00,
    subscribed: false
  };

  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));

  // ─── 1. COUNTDOWN (24h, localStorage-persisted, never zeroes) ───
  function initCountdown() {
    const KEY = 'em_countdown_end';
    let end = parseInt(localStorage.getItem(KEY) || '0', 10);
    if (!end || end < Date.now()) {
      end = Date.now() + CONFIG.countdownHours * 3600 * 1000;
      localStorage.setItem(KEY, String(end));
    }
    const segs = {
      d: $('[data-cd="d"]'), h: $('[data-cd="h"]'),
      m: $('[data-cd="m"]'), s: $('[data-cd="s"]')
    };
    const pad = n => String(n).padStart(2, '0');
    function tick() {
      let r = Math.max(1000, end - Date.now());
      const d = Math.floor(r / 86400000);
      const h = Math.floor((r % 86400000) / 3600000);
      const m = Math.floor((r % 3600000) / 60000);
      const s = Math.floor((r % 60000) / 1000);
      // update only the textContent without nuking the .lbl span
      function setSeg(el, val) {
        if (!el) return;
        const lbl = el.querySelector('.lbl');
        el.firstChild.nodeValue = pad(val);
        if (lbl && el.firstChild === lbl) {
          // safety: rebuild
          el.innerHTML = pad(val) + '<span class="lbl">' + lbl.textContent + '</span>';
        }
      }
      setSeg(segs.d, d); setSeg(segs.h, h); setSeg(segs.m, m); setSeg(segs.s, s);
      if (end - Date.now() <= 1000) {
        end = Date.now() + CONFIG.countdownHours * 3600 * 1000;
        localStorage.setItem(KEY, String(end));
      }
    }
    tick();
    setInterval(tick, 1000);
  }

  // ─── 2. RESERVATION TIMER (10 min, resets each load) ───
  function initReservation() {
    const el = $('#reserve-time');
    if (!el) return;
    let secs = CONFIG.reservationMinutes * 60;
    function tick() {
      secs = Math.max(60, secs - 1); // floor at 1:00 so we never expire
      const m = Math.floor(secs / 60);
      const s = secs % 60;
      el.textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
    }
    tick();
    setInterval(tick, 1000);
  }

  // ─── 3. DYNAMIC SHIP DATE (8 days from now) ───
  function initShipDate() {
    const el = $('#ship-date');
    if (!el) return;
    const d = new Date();
    d.setDate(d.getDate() + 8);
    const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    el.textContent = `${days[d.getDay()]}, ${months[d.getMonth()]} ${d.getDate()}`;
  }

  // ─── 4. BUNDLE SELECTOR ───
  function initTiers() {
    const tiers = $$('.tier');
    tiers.forEach((t, i) => {
      t.addEventListener('click', e => {
        e.preventDefault();
        tiers.forEach(x => x.classList.remove('active'));
        t.classList.add('active');
        state.bundleIdx = i;
        state.count = parseInt(t.dataset.count, 10);
        state.each = parseFloat(t.dataset.each);
        recalc();
      });
    });
  }

  // ─── 5. SUBSCRIBE TOGGLE ───
  function initSubscribe() {
    const tog = $('#sub-toggle');
    const savings = $('#sub-savings');
    if (!tog) return;
    tog.addEventListener('click', e => {
      e.preventDefault();
      state.subscribed = !state.subscribed;
      tog.classList.toggle('on', state.subscribed);
      if (savings) savings.hidden = !state.subscribed;
      recalc();
    });
  }

  // ─── 6. RECALC TOTALS / FREEBIES / CTA ───
  function fmt(n) { return '$' + n.toFixed(2); }
  function recalc() {
    const subtotal = state.each * state.count;
    const final = state.subscribed ? subtotal * (1 - CONFIG.subscribeDiscount) : subtotal;

    const subLabel = $('#subtotal-label');
    const subVal = $('#subtotal-value');
    const totalVal = $('#total-value');
    const ship = $('#shipping-line');
    const ctaStrike = $('#cta-strike');
    const ctaNow = $('#cta-now');
    const freebies = $('#freebies');
    const mobileCta = $('.mobile-cta');

    if (subLabel) subLabel.textContent = `${fmt(state.each)} × ${state.count}`;
    if (subVal) subVal.textContent = fmt(subtotal);
    if (totalVal) totalVal.textContent = fmt(final);

    // Free shipping on 2x and 3x; otherwise show $5 shipping
    const shipFree = state.count >= 2;
    if (ship) {
      ship.textContent = shipFree ? 'FREE' : '$5.00';
      ship.classList.toggle('free', shipFree);
    }

    // CTA: anchor strike based on count × $34, current is final
    if (ctaStrike) ctaStrike.textContent = fmt(CONFIG.anchorPrice * state.count);
    if (ctaNow) ctaNow.textContent = fmt(final);

    // Tiered gift unlock — locked unless bundle count >= gift's data-min-count
    const giftStack = document.getElementById('gift-stack');
    if (giftStack) {
      giftStack.dataset.count = String(state.count);
      giftStack.querySelectorAll('.gift').forEach(g => {
        const min = parseInt(g.dataset.minCount || '99', 10);
        const unlocked = state.count >= min;
        g.classList.toggle('unlocked', unlocked);
        const thresh = g.querySelector('.gift-thresh');
        if (thresh) {
          thresh.textContent = unlocked ? '✓ Included' : `Unlocks at ${min} bottles`;
        }
      });
    }
    // Legacy freebies row — keep hidden, replaced by gift-stack
    if (freebies) freebies.style.display = 'none';

    // Mobile CTA mini-pricing
    if (mobileCta) {
      mobileCta.innerHTML = `<span><strong>Claim Offer</strong> <span style="opacity:0.7;text-decoration:line-through;font-weight:400;">${fmt(CONFIG.anchorPrice * state.count)}</span> ${fmt(final)}</span><span>→</span>`;
    }
  }

  // ─── 7. TAB SWITCHER ───
  function initTabs() {
    const tabs = $$('.tab');
    const panels = $$('.tab-panel');
    tabs.forEach(t => t.addEventListener('click', e => {
      e.preventDefault();
      const target = t.dataset.tab;
      tabs.forEach(x => x.classList.toggle('active', x === t));
      panels.forEach(p => p.hidden = p.dataset.panel !== target);
    }));
  }

  // ─── 8. FAQ ACCORDION ───
  function initFAQ() {
    $$('.faq-item').forEach(item => {
      const q = item.querySelector('.faq-q');
      const a = item.querySelector('.faq-a');
      q.addEventListener('click', e => {
        e.preventDefault();
        const isOpen = item.classList.contains('open');
        if (isOpen) {
          a.style.maxHeight = '0px';
          item.classList.remove('open');
        } else {
          a.style.maxHeight = a.scrollHeight + 'px';
          item.classList.add('open');
        }
      });
    });
  }

  // ─── 9. HERO GALLERY — swap photo + live HTML overlay (selectable text) ───
  // Overlay content is REAL HTML — selectable, accessible, SEO-indexable.
  // Each photo carries its own conversion message via data-overlay key.
  const OVERLAYS = {
    bottle: `
      <div class="hero-badge corner-tl"><span class="badge-pill">JUICY &amp; VIBRANT</span></div>
      <div class="hero-stat corner-tr"><span class="stat-num">+137%</span><span class="stat-lbl">moisture</span></div>
      <div class="hero-caption corner-bl">
        <div class="hero-caption-title">Berry Obsessed</div>
        <div class="hero-caption-sub">Strawberry · Cream · Vanilla</div>
      </div>`,
    strawberry: `
      <div class="hero-badge corner-tl"><span class="badge-pill badge-coral">WILD STRAWBERRY</span></div>
      <div class="hero-stat corner-tr"><span class="stat-num">12 hr</span><span class="stat-lbl">scent lock</span></div>
      <div class="hero-caption corner-bl">
        <div class="hero-caption-title">$130 vibe.</div>
        <div class="hero-caption-sub">$22 price tag.</div>
      </div>
      <div class="hero-chips corner-br">
        <span class="chip">TOP</span><span class="chip">HEART</span><span class="chip">BASE</span>
      </div>`,
    lifestyle: `
      <div class="hero-badge corner-tl"><span class="badge-pill badge-dark">REAL CUSTOMER</span></div>
      <div class="hero-stat corner-tr"><span class="stat-num">96%</span><span class="stat-lbl">got compliments</span></div>
      <div class="hero-caption corner-bl">
        <div class="hero-caption-quote">&ldquo;Got 4 compliments at brunch.&rdquo;</div>
        <div class="hero-caption-attr">— JESS T. · VERIFIED BUYER</div>
      </div>`,
    ingredients: `
      <div class="hero-badge corner-tl"><span class="badge-pill">INSIDE EVERY SPRITZ</span></div>
      <div class="hero-stat corner-tr"><span class="stat-num">0%</span><span class="stat-lbl">denatured alcohol</span></div>
      <div class="hero-chips corner-bl chips-stack">
        <span class="chip chip-coral">Hyaluronic Acid</span>
        <span class="chip chip-coral">Coconut Extract</span>
        <span class="chip chip-coral">Vitamin E</span>
      </div>`,
    closeup: `
      <div class="hero-badge corner-tl"><span class="badge-pill">100mL · 3.4 fl oz</span></div>
      <div class="hero-stat corner-tr"><span class="stat-num">~600</span><span class="stat-lbl">spritzes</span></div>
      <div class="hero-caption corner-bl">
        <div class="hero-caption-title">Pocket-sized.</div>
        <div class="hero-caption-sub">Dermatologist tested · Vegan · Cruelty-free</div>
      </div>`,
    dramatic: `
      <div class="hero-badge corner-tl"><span class="badge-pill badge-lime">55% OFF · LIMITED</span></div>
      <div class="hero-caption corner-bl">
        <div class="hero-caption-title"><span class="strike">$34</span> &nbsp;$22</div>
        <div class="hero-caption-sub">+ free Mystery Mini on the 3-pack</div>
      </div>`,
  };

  function initThumbs() {
    const thumbs = $$('.hero-thumb');
    const mainImg = $('#hero-main-img');
    const overlay = $('#hero-overlay');
    function swap(t) {
      thumbs.forEach(x => x.classList.toggle('active', x === t));
      const newSrc = t.dataset.src;
      const stage = t.dataset.overlay;
      if (mainImg && newSrc && mainImg.getAttribute('src') !== newSrc) {
        mainImg.classList.add('swapping');
        setTimeout(() => {
          mainImg.setAttribute('src', newSrc);
          mainImg.onload = () => mainImg.classList.remove('swapping');
        }, 120);
      }
      if (overlay && stage && OVERLAYS[stage]) {
        overlay.classList.add('overlay-fade');
        setTimeout(() => {
          overlay.dataset.overlay = stage;
          overlay.innerHTML = OVERLAYS[stage];
          overlay.classList.remove('overlay-fade');
        }, 160);
      }
    }
    thumbs.forEach(t => t.addEventListener('click', e => {
      e.preventDefault();
      swap(t);
    }));
  }

  // ─── 10. UPSELL MODAL ───
  function openUpsell() {
    if ($('#modal-backdrop')) return;
    const u = CONFIG.upsell;
    const save = (u.original - u.price).toFixed(2);
    const m = document.createElement('div');
    m.id = 'modal-backdrop';
    m.innerHTML = `
      <div class="modal-card" role="dialog" aria-modal="true">
        <button class="modal-close" aria-label="Close">×</button>
        <div class="body">
          <span class="modal-tag">★ COMMUNITY FAVORITE ADD-ON</span>
          <div class="modal-product modal-product-photo">
            <img src="${u.img}" alt="${u.name} bottle" loading="lazy">
          </div>
          <div class="modal-mood">${u.mood} mood · <span style="color:#FFB800">★★★★★</span> <span style="color:#6b7280">(4.8/5)</span></div>
          <h3>${u.name}</h3>
          <div class="modal-tagline">${u.tagline}</div>
          <div class="modal-prices">
            <span class="strike">$${u.original.toFixed(2)}</span>
            <span class="now">$${u.price.toFixed(2)}</span>
            <span class="save">Save $${save}</span>
          </div>
          <ul>
            ${u.bullets.map(b => '<li>' + b + '</li>').join('')}
          </ul>
          <div class="timer-bar">⏱ Discount expires in <span id="modal-timer">14:59</span></div>
          <button class="add-btn" id="modal-add-btn" type="button">
            <span class="add-btn-default">+ Add ${u.name} to order &nbsp;·&nbsp; one click</span>
            <span class="add-btn-success">✓ Added to your order</span>
          </button>
          <a class="decline-btn" href="${CONFIG.checkoutUrl}">No thanks, continue to check-out</a>
        </div>
      </div>
    `;
    document.body.appendChild(m);
    let secs = 15 * 60 - 1;
    const tEl = m.querySelector('#modal-timer');
    const ti = setInterval(() => {
      secs = Math.max(0, secs - 1);
      const mn = Math.floor(secs / 60), sc = secs % 60;
      if (tEl) tEl.textContent = `${mn}:${String(sc).padStart(2,'0')}`;
      if (secs === 0) clearInterval(ti);
    }, 1000);
    function close() { clearInterval(ti); m.remove(); }
    m.querySelector('.modal-close').addEventListener('click', close);
    m.addEventListener('click', e => { if (e.target === m) close(); });
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });

    // ─── ONE-CLICK ADD ───
    // Single-click adds the upsell to the order without navigating away.
    // (When you wire up Shopify, swap the simulated state update for a real
    // POST to /cart/add.js.)
    const addBtn = m.querySelector('#modal-add-btn');
    addBtn.addEventListener('click', () => {
      if (addBtn.classList.contains('added')) return;
      addBtn.classList.add('adding');
      // Simulated add — replace with fetch('/cart/add.js', {...}) when live
      setTimeout(() => {
        addBtn.classList.remove('adding');
        addBtn.classList.add('added');
        // Track in state so a future "your order" view can read it
        window.__em.upsellAdded = u.name;
        // Auto-close after a beat so they see the confirmation
        setTimeout(close, 1600);
      }, 350);
    });
  }

  function initCTAs() {
    $$('[data-cta]').forEach(b => b.addEventListener('click', e => {
      e.preventDefault();
      openUpsell();
    }));
  }

  // ─── BOOT ───
  function boot() {
    try { initCountdown(); } catch (e) { console.warn('cd', e); }
    try { initReservation(); } catch (e) { console.warn('rv', e); }
    try { initShipDate(); } catch (e) { console.warn('sd', e); }
    try { initTiers(); } catch (e) { console.warn('tr', e); }
    try { initSubscribe(); } catch (e) { console.warn('sb', e); }
    try { initTabs(); } catch (e) { console.warn('tb', e); }
    try { initFAQ(); } catch (e) { console.warn('faq', e); }
    try { initThumbs(); } catch (e) { console.warn('th', e); }
    try { initCTAs(); } catch (e) { console.warn('cta', e); }
    try { recalc(); } catch (e) { console.warn('rc', e); }
    try { initLadderReveal(); } catch (e) { console.warn('lad', e); }
    console.log('[everymood] interactivity loaded');
  }

  // ── Ladder bar reveal: trigger CSS bar fill when ladder enters viewport ──
  function initLadderReveal() {
    var rows = Array.prototype.slice.call(document.querySelectorAll('.ladder-row'));
    if (!rows.length) return;
    if (!('IntersectionObserver' in window)) {
      rows.forEach(function (r) { r.classList.add('is-visible'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          var idx = rows.indexOf(e.target);
          setTimeout(function () { e.target.classList.add('is-visible'); }, idx * 120);
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.25, rootMargin: '0px 0px -10% 0px' });
    rows.forEach(function (r) { io.observe(r); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
