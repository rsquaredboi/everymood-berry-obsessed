/**
 * Smooche clone interactivity layer
 * Wires up all features that the live React app handles, in vanilla JS.
 *
 * Features:
 *  1. Countdown timer (24h, persists via localStorage)
 *  2. FAQ accordion (8 questions, click to expand/collapse)
 *  3. Bundle selector (1x/2x/3x — visual select + total recalc)
 *  4. Subscribe & Save toggle (~11% discount, changes frequency label)
 *  5. Tab switcher (Benefits / Why Smooche / How It Works)
 *  6. Claim Offer CTA → upsell modal → checkout
 *
 * Replace [PLACEHOLDER] strings with your own copy.
 */
(() => {
  'use strict';

  // ─────────────────────────────────────────────────────────
  // CONFIG — edit these
  // ─────────────────────────────────────────────────────────
  const CONFIG = {
    countdownHours: 24,                 // resets every N hours
    subscribeDiscount: 0.11,            // 11% off
    checkoutUrl: '#checkout',           // where Claim Offer + Add to order goes
    upsellPrice: 'HK$152.00',           // cross-sell product price
    upsellOriginalPrice: 'HK$231.00',
    upsellSave: 'Save HK$79.00'
  };

  const FAQ_ANSWERS = {
    "What makes this a 'Korean pharmacy' foundation?": "[Add your answer here — replace with your own copy.]",
    "How does the anti-aging formula work?": "[Add your answer here — replace with your own copy.]",
    "Can it really replace Botox?": "[Add your answer here — replace with your own copy.]",
    "Does it work on crepey neck skin?": "[Add your answer here — replace with your own copy.]",
    "Will it fade my dark spots?": "[Add your answer here — replace with your own copy.]",
    "Does it work on my skin tone?": "[Add your answer here — replace with your own copy.]",
    "How does the money back guarantee work?": "[Add your answer here — replace with your own copy.]",
    "Where do you ship to?": "[Add your answer here — replace with your own copy.]"
  };

  // Tab panel content (only Benefits is rendered in the static HTML)
  const TAB_PANELS = {
    'Benefits': null,                   // null = use whatever is already in the DOM
    'Why Smooche': '[Add your "Why Smooche" content here — bullet points that explain why your product wins.]',
    'How It Works': '[Add your "How It Works" content here — step 1, step 2, step 3.]'
  };

  // ─────────────────────────────────────────────────────────
  // 1. COUNTDOWN TIMER
  // ─────────────────────────────────────────────────────────
  function initCountdown() {
    const KEY = 'smooche_countdown_end';
    let end = parseInt(localStorage.getItem(KEY) || '0', 10);
    const now = Date.now();
    if (!end || end < now) {
      end = now + CONFIG.countdownHours * 3600 * 1000;
      localStorage.setItem(KEY, String(end));
    }

    const digits = Array.from(document.querySelectorAll('span'))
      .filter(s => /^\d{2}$/.test(s.textContent.trim()) && s.children.length === 0)
      .slice(0, 4);
    if (digits.length !== 4) {
      console.warn('Countdown: expected 4 digit spans, found', digits.length);
      return;
    }

    const pad = n => String(n).padStart(2, '0');
    function tick() {
      let remain = Math.max(1000, end - Date.now()); // never show 00:00:00:00
      const days = Math.floor(remain / 86400000);
      const hrs = Math.floor((remain % 86400000) / 3600000);
      const mins = Math.floor((remain % 3600000) / 60000);
      const secs = Math.floor((remain % 60000) / 1000);
      digits[0].textContent = pad(days);
      digits[1].textContent = pad(hrs);
      digits[2].textContent = pad(mins);
      digits[3].textContent = pad(secs);
      if (end - Date.now() <= 1000) {
        end = Date.now() + CONFIG.countdownHours * 3600 * 1000;
        localStorage.setItem(KEY, String(end));
      }
    }
    tick();
    setInterval(tick, 1000);
  }

  // ─────────────────────────────────────────────────────────
  // 2. FAQ ACCORDION
  // ─────────────────────────────────────────────────────────
  function initFAQ() {
    const buttons = Array.from(document.querySelectorAll('button'))
      .filter(b => b.querySelector('.lucide-chevron-down'));

    buttons.forEach(btn => {
      const q = btn.querySelector('span')?.textContent?.trim() || btn.textContent.trim();
      const answer = FAQ_ANSWERS[q] || '[Add your answer here.]';

      const ans = document.createElement('div');
      ans.className = 'faq-answer';
      ans.style.cssText = 'max-height:0;overflow:hidden;transition:max-height 0.35s ease;';
      ans.innerHTML = `<p style="padding:0 0 16px 0;color:#4b5563;font-size:0.95rem;line-height:1.6;">${answer}</p>`;
      btn.parentElement.appendChild(ans);

      const chev = btn.querySelector('.lucide-chevron-down');
      if (chev) chev.style.transition = 'transform 0.3s ease';

      btn.addEventListener('click', e => {
        e.preventDefault();
        const open = ans.style.maxHeight && ans.style.maxHeight !== '0px';
        if (open) {
          ans.style.maxHeight = '0px';
          if (chev) chev.style.transform = 'rotate(0deg)';
        } else {
          ans.style.maxHeight = ans.scrollHeight + 'px';
          if (chev) chev.style.transform = 'rotate(180deg)';
        }
      });
    });
  }

  // ─────────────────────────────────────────────────────────
  // 3. BUNDLE SELECTOR
  // ─────────────────────────────────────────────────────────
  function initBundleSelector() {
    const bundles = Array.from(document.querySelectorAll('button'))
      .filter(b => /Bottles?HK?\$/.test(b.textContent.replace(/\s/g, '')));
    if (bundles.length < 2) return;

    // Parse per-bottle price + bottle count from each button
    const bundleData = bundles.map(b => {
      const txt = b.textContent;
      const countMatch = txt.match(/(\d+)\s*Bottles?/);
      const priceMatch = txt.match(/(?:HK)?\$([\d,]+\.\d{2})/);
      return {
        el: b,
        count: countMatch ? parseInt(countMatch[1], 10) : 1,
        unitPrice: priceMatch ? parseFloat(priceMatch[1].replace(/,/g, '')) : 0
      };
    });

    // Find Total + Claim Offer button
    function setActive(idx) {
      bundleData.forEach((bd, i) => {
        const isActive = i === idx;
        bd.el.style.borderColor = isActive ? '#C75B7A' : 'transparent';
        bd.el.style.borderWidth = '2px';
        bd.el.style.backgroundColor = isActive ? '#fef2f4' : 'white';
      });
      const total = bundleData[idx].unitPrice * bundleData[idx].count;
      window.__smoocheState = window.__smoocheState || {};
      window.__smoocheState.bundleIdx = idx;
      window.__smoocheState.totalBase = total;
      updateTotalDisplay();
    }

    bundleData.forEach((bd, i) => {
      bd.el.style.cursor = 'pointer';
      bd.el.addEventListener('click', e => {
        e.preventDefault();
        setActive(i);
      });
    });

    // Default: 3x (BEST DEAL) is selected per the visual default
    const defaultIdx = bundleData.length === 3 ? 2 : 0;
    setActive(defaultIdx);
  }

  function fmtHK(n) {
    return 'HK$' + n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  function updateTotalDisplay() {
    const state = window.__smoocheState || {};
    const baseTotal = state.totalBase || 0;
    const subscribed = !!state.subscribed;
    const final = subscribed ? baseTotal * (1 - CONFIG.subscribeDiscount) : baseTotal;

    // Update "Claim Offer" button text — preserve original prefix + strikethrough
    const claimBtn = Array.from(document.querySelectorAll('button'))
      .find(b => /^Claim Offer/.test(b.textContent.trim()) && !/Now/.test(b.textContent));
    if (claimBtn) {
      // The button text looks like "Claim OfferHK$469.00HK$310.00"
      // We rewrite cleanly with two prices side-by-side
      const original = baseTotal * 1.51; // approximation of strike price
      claimBtn.innerHTML = `Claim Offer&nbsp;<span style="text-decoration:line-through;opacity:0.7;font-weight:400;">${fmtHK(original)}</span>&nbsp;${fmtHK(final)}<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-left:8px;"><path d="m9 18 6-6-6-6"></path></svg>`;
    }

    // Update Total row — find <span>Total</span> and update its sibling
    const totalLabel = Array.from(document.querySelectorAll('span'))
      .find(el => el.children.length === 0 && el.textContent.trim() === 'Total');
    if (totalLabel) {
      const valEl = totalLabel.nextElementSibling;
      if (valEl && /HK\$/.test(valEl.textContent)) {
        valEl.textContent = fmtHK(final);
      }
    }

    // Update subtotal line "HK$XXX × N"
    const bundle = state.bundleIdx != null ? state.bundleIdx : 0;
    const count = bundle === 0 ? 1 : bundle === 1 ? 2 : 3;
    const unit = baseTotal / count;
    const subtotalEl = Array.from(document.querySelectorAll('span'))
      .find(el => el.children.length === 0 && /HK\$[\d,.]+ × \d+/.test(el.textContent));
    if (subtotalEl) {
      subtotalEl.textContent = `${fmtHK(unit)} × ${count}`;
      // Also update the price on the right side of that subtotal row
      const subVal = subtotalEl.nextElementSibling;
      if (subVal && /HK\$/.test(subVal.textContent)) {
        subVal.textContent = fmtHK(baseTotal);
      }
    }

    // Show / hide freebies row (3x bundle only)
    updateFreebies(count);
  }

  // ─────────────────────────────────────────────────────────
  // Freebies row (shown for 3x bundle only)
  // ─────────────────────────────────────────────────────────
  function updateFreebies(bottleCount) {
    let row = document.getElementById('smooche-freebies');
    if (!row) {
      // Find the price summary box (the box containing the Total row) and append freebies above it
      const totalLabel = Array.from(document.querySelectorAll('span'))
        .find(el => el.children.length === 0 && el.textContent.trim() === 'Total');
      if (!totalLabel) return;
      // The price summary box is a few levels up
      const priceBox = totalLabel.closest('.border, [class*="border"]');
      if (!priceBox) return;
      row = document.createElement('div');
      row.id = 'smooche-freebies';
      row.style.cssText = 'display:none;grid-template-columns:repeat(3, 1fr);gap:8px;margin-top:14px;text-align:center;';
      row.innerHTML = `
        <div style="background:#fef3c7;border-radius:8px;padding:10px 6px;">
          <div style="font-size:24px;line-height:1;margin-bottom:4px;">📦</div>
          <div style="font-size:10px;font-weight:700;color:#b91c1c;letter-spacing:0.3px;">FREE SHIPPING</div>
        </div>
        <div style="background:#fce7f3;border-radius:8px;padding:10px 6px;">
          <div style="font-size:24px;line-height:1;margin-bottom:4px;">🎁</div>
          <div style="font-size:10px;font-weight:700;color:#b91c1c;letter-spacing:0.3px;">FREE MYSTERY GIFT</div>
        </div>
        <div style="background:#fed7aa;border-radius:8px;padding:10px 6px;">
          <div style="font-size:24px;line-height:1;margin-bottom:4px;">💄</div>
          <div style="font-size:10px;font-weight:700;color:#b91c1c;letter-spacing:0.3px;">FREE BONUS ITEM</div>
        </div>
      `;
      priceBox.parentElement.insertBefore(row, priceBox.nextSibling);
    }
    row.style.display = bottleCount === 3 ? 'grid' : 'none';
  }

  // ─────────────────────────────────────────────────────────
  // 4. SUBSCRIBE & SAVE TOGGLE
  // ─────────────────────────────────────────────────────────
  function initSubscribeToggle() {
    const subBtn = Array.from(document.querySelectorAll('button'))
      .find(b => /Subscribe.*Save/i.test(b.textContent));
    if (!subBtn) return;

    // Use the EXISTING React-rendered toggle pill (don't add a duplicate)
    const toggleTrack = subBtn.querySelector('.rounded-full');
    const toggleKnob = toggleTrack?.querySelector('div');
    if (!toggleTrack || !toggleKnob) {
      console.warn('subscribe: existing toggle not found');
      return;
    }
    toggleTrack.style.transition = 'background-color 0.2s';
    toggleKnob.style.transition = 'transform 0.2s';

    // Find the "Subscribe & Save 15%" label so we can update the percentage
    const subLabel = subBtn.querySelector('p.font-bold');
    const labelTpl = subLabel ? subLabel.textContent.replace(/\d+%/, '{P}%') : null;

    function setSubscribed(on) {
      window.__smoocheState = window.__smoocheState || {};
      window.__smoocheState.subscribed = on;
      // Update the existing toggle styles
      toggleTrack.classList.remove('bg-gray-300');
      toggleTrack.style.backgroundColor = on ? '#C75B7A' : '#d1d5db';
      toggleKnob.style.transform = on ? 'translateX(18px)' : 'translateX(2px)';
      // Update label percentage to match actual discount
      if (subLabel && labelTpl) {
        subLabel.textContent = labelTpl.replace('{P}', String(Math.round(CONFIG.subscribeDiscount * 100)));
      }
      updateTotalDisplay();
    }

    subBtn.style.cursor = 'pointer';
    subBtn.addEventListener('click', e => {
      e.preventDefault();
      const cur = !!(window.__smoocheState && window.__smoocheState.subscribed);
      setSubscribed(!cur);
    });
    setSubscribed(false);
  }

  // ─────────────────────────────────────────────────────────
  // 5. TAB SWITCHER
  // ─────────────────────────────────────────────────────────
  function initTabSwitcher() {
    const tabNames = ['Benefits', 'Why Smooche', 'How It Works'];
    const tabBtns = tabNames.map(name =>
      Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === name)
    ).filter(Boolean);
    if (tabBtns.length < 2) return;

    // The Benefits panel is the existing list right after the tabs (a <ul> or <div> with the bullets)
    const tabsContainer = tabBtns[0].parentElement;
    const benefitsPanel = tabsContainer?.nextElementSibling;
    if (!benefitsPanel) return;

    // Save the original Benefits HTML once so we can restore it
    const originalBenefitsHTML = benefitsPanel.innerHTML;

    function activate(idx) {
      tabBtns.forEach((b, i) => {
        const active = i === idx;
        b.style.color = active ? '#C75B7A' : '#6b7280';
        b.style.borderBottom = active ? '2px solid #C75B7A' : '2px solid transparent';
        b.style.fontWeight = active ? '700' : '500';
      });
      const name = tabNames[idx];
      const customContent = TAB_PANELS[name];
      if (name === 'Benefits' || customContent === null) {
        benefitsPanel.innerHTML = originalBenefitsHTML;
      } else {
        benefitsPanel.innerHTML = `<div style="padding:8px 0;color:#4b5563;font-size:0.95rem;line-height:1.6;">${customContent}</div>`;
      }
    }

    tabBtns.forEach((b, i) => {
      b.style.cursor = 'pointer';
      b.style.transition = 'color 0.15s, border 0.15s';
      b.addEventListener('click', e => {
        e.preventDefault();
        activate(i);
      });
    });
    activate(0);
  }

  // ─────────────────────────────────────────────────────────
  // 6. CLAIM OFFER → UPSELL MODAL → CHECKOUT
  // ─────────────────────────────────────────────────────────
  function initCTAFlow() {
    function openUpsellModal() {
      // If already open, do nothing
      if (document.getElementById('smooche-upsell-modal')) return;

      const modal = document.createElement('div');
      modal.id = 'smooche-upsell-modal';
      modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.55);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;';

      modal.innerHTML = `
        <div style="background:white;max-width:420px;width:100%;border-radius:14px;overflow:hidden;box-shadow:0 25px 50px -12px rgba(0,0,0,0.4);position:relative;font-family:'DM Sans',sans-serif;">
          <button id="smooche-upsell-close" aria-label="Close" style="position:absolute;top:12px;right:12px;background:rgba(0,0,0,0.05);border:0;width:32px;height:32px;border-radius:50%;font-size:18px;cursor:pointer;line-height:1;z-index:1;">×</button>
          <div style="padding:14px 20px 0 20px;">
            <div style="display:inline-block;background:#fde68a;color:#92400e;font-size:11px;font-weight:700;padding:4px 10px;border-radius:999px;letter-spacing:0.5px;text-transform:uppercase;">★ Our community favorite</div>
          </div>
          <div style="padding:14px 20px 20px 20px;text-align:center;">
            <div style="height:140px;background:#fff7ed;border-radius:8px;margin-bottom:14px;display:flex;align-items:center;justify-content:center;color:#9ca3af;font-size:13px;">[ Add cross-sell product image here ]</div>
            <div style="color:#f59e0b;font-size:13px;margin-bottom:6px;">★★★★★ &nbsp;<span style="color:#6b7280;">(4.8/5)</span></div>
            <h3 style="font-family:Futura,Trebuchet MS,Arial,sans-serif;font-size:1.15rem;font-weight:700;margin:0 0 10px 0;color:#111;">[Cross-sell product name]</h3>
            <div style="margin-bottom:14px;">
              <span style="color:#9ca3af;text-decoration:line-through;font-size:0.95rem;">${CONFIG.upsellOriginalPrice}</span>
              &nbsp;<span style="color:#111;font-weight:700;font-size:1.05rem;">${CONFIG.upsellPrice}</span>
              &nbsp;<span style="background:#fee2e2;color:#b91c1c;font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;">${CONFIG.upsellSave}</span>
            </div>
            <ul style="text-align:left;color:#4b5563;font-size:0.9rem;line-height:1.55;padding-left:18px;margin:0 0 14px 0;">
              <li>[Cross-sell benefit bullet 1]</li>
              <li>[Cross-sell benefit bullet 2]</li>
              <li>[Cross-sell benefit bullet 3]</li>
            </ul>
            <div style="background:#fef3c7;color:#92400e;font-size:12px;font-weight:600;padding:6px 10px;border-radius:6px;margin-bottom:14px;">Discount expires in <span id="smooche-upsell-timer">14:59</span></div>
            <a href="${CONFIG.checkoutUrl}?upsell=1" id="smooche-upsell-add" style="display:block;background:#111;color:white;text-decoration:none;padding:14px;border-radius:8px;font-weight:700;font-size:0.95rem;margin-bottom:10px;">Add to order with discount</a>
            <a href="${CONFIG.checkoutUrl}" id="smooche-upsell-decline" style="display:block;color:#6b7280;text-decoration:underline;font-size:0.9rem;padding:6px;">No thanks, continue to check-out</a>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      // 15-min upsell timer (resets per modal open)
      let upsellRemain = 15 * 60;
      const tEl = modal.querySelector('#smooche-upsell-timer');
      const upsellInterval = setInterval(() => {
        upsellRemain = Math.max(0, upsellRemain - 1);
        const m = Math.floor(upsellRemain / 60);
        const s = upsellRemain % 60;
        if (tEl) tEl.textContent = `${m}:${String(s).padStart(2, '0')}`;
        if (upsellRemain === 0) clearInterval(upsellInterval);
      }, 1000);

      function close() {
        clearInterval(upsellInterval);
        modal.remove();
      }
      modal.querySelector('#smooche-upsell-close').addEventListener('click', close);
      modal.addEventListener('click', e => { if (e.target === modal) close(); });
    }

    // Bind to ALL "Claim Offer*" buttons (hero + bottom CTA)
    document.querySelectorAll('button').forEach(b => {
      const t = b.textContent.trim();
      if (/^Claim Offer/i.test(t) || /^Claim Your Offer Now/i.test(t)) {
        b.style.cursor = 'pointer';
        b.addEventListener('click', e => {
          e.preventDefault();
          openUpsellModal();
        });
      }
    });
  }

  // ─────────────────────────────────────────────────────────
  // BOOT
  // ─────────────────────────────────────────────────────────
  function boot() {
    try { initCountdown(); } catch (e) { console.warn('countdown failed', e); }
    try { initFAQ(); } catch (e) { console.warn('faq failed', e); }
    try { initTabSwitcher(); } catch (e) { console.warn('tabs failed', e); }
    try { initBundleSelector(); } catch (e) { console.warn('bundles failed', e); }
    try { initSubscribeToggle(); } catch (e) { console.warn('subscribe failed', e); }
    try { initCTAFlow(); } catch (e) { console.warn('cta failed', e); }
    console.log('[smooche] interactivity loaded');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
