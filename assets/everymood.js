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
      name: 'Travel Berry Mini (50mL)',
      desc: 'Toss it in your bag. The Berry Obsessed scent in pocket size.',
      price: 14.00,
      original: 22.00,
      bullets: [
        'Same skincare-first formula, smaller bottle',
        'TSA-approved for carry-on travel',
        'Refillable from your full-size bottle'
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

  // ─── 9. HERO THUMBNAIL STRIP — swap main image on click ───
  function initThumbs() {
    const thumbs = $$('.hero-thumb');
    const mainImg = $('#hero-main-img');
    thumbs.forEach(t => t.addEventListener('click', e => {
      e.preventDefault();
      thumbs.forEach(x => x.classList.toggle('active', x === t));
      const newSrc = t.dataset.src;
      if (mainImg && newSrc && mainImg.getAttribute('src') !== newSrc) {
        mainImg.classList.add('swapping');
        // tiny delay so the fade is visible
        setTimeout(() => {
          mainImg.setAttribute('src', newSrc);
          mainImg.onload = () => mainImg.classList.remove('swapping');
        }, 120);
      }
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
          <div class="modal-product" style="margin-top:14px;">🍓</div>
          <div style="color:#FFB800;font-size:13px;margin-top:12px;">★★★★★ <span style="color:#6b7280">(4.8/5)</span></div>
          <h3>${u.name}</h3>
          <div class="modal-prices">
            <span class="strike">$${u.original.toFixed(2)}</span>
            <span class="now">$${u.price.toFixed(2)}</span>
            <span class="save">Save $${save}</span>
          </div>
          <ul>
            ${u.bullets.map(b => '<li>' + b + '</li>').join('')}
          </ul>
          <div class="timer-bar">⏱ Discount expires in <span id="modal-timer">14:59</span></div>
          <a class="add-btn" href="${CONFIG.checkoutUrl}?upsell=1">Add to order with discount →</a>
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
    console.log('[everymood] interactivity loaded');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
