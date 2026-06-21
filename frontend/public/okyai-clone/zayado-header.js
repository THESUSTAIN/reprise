/* ==========================================================================
   ZAYADO HEADER ENHANCE  (v2)
   - Theme toggle (moon/sun)
   - Messages + Mail + Bell dropdowns (real panels, not alerts)
   - Profile dropdown : Account User · Profile · Settings · Billing & Plans · Logout
   - All popovers close on outside-click / Escape
   ========================================================================== */
(function () {
  'use strict';

  const THEME_KEY = 'zayado-theme';

  /* ------------ THEME ------------ */
  function applyTheme(theme) {
    const html = document.documentElement;
    if (theme === 'light') html.classList.remove('dark');
    else html.classList.add('dark');
    localStorage.setItem(THEME_KEY, theme);
    updateToggleIcon();
  }
  function currentTheme() { return localStorage.getItem(THEME_KEY) || 'dark'; }
  function updateToggleIcon() {
    const btn = document.querySelector('[data-zayado-theme-toggle]');
    if (!btn) return;
    const isDark = document.documentElement.classList.contains('dark');
    btn.innerHTML = `<i data-lucide="${isDark ? 'sun' : 'moon'}" class="size-5" aria-hidden="true"></i>`;
    if (window.lucide?.createIcons) window.lucide.createIcons();
  }

  /* ------------ POPOVERS ------------ */
  // Single registry — closing one closes the others.
  const registry = new Set();
  function closeAll(except) {
    registry.forEach((p) => { if (p !== except) p.close(); });
  }
  document.addEventListener('click', (e) => {
    // If click happens outside any open popover & their triggers — close all
    let hit = false;
    registry.forEach((p) => {
      if (p.el.contains(e.target) || p.trigger.contains(e.target)) hit = true;
    });
    if (!hit) closeAll(null);
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeAll(null); });

  function makePopover(trigger, contentHtml, opts = {}) {
    const el = document.createElement('div');
    el.className = 'zy-popover';
    el.setAttribute('role', 'dialog');
    el.innerHTML = contentHtml;
    el.style.display = 'none';
    document.body.appendChild(el);

    const obj = {
      el,
      trigger,
      open() {
        closeAll(obj);
        position();
        el.style.display = 'block';
        requestAnimationFrame(() => el.classList.add('zy-popover-open'));
        trigger.setAttribute('aria-expanded', 'true');
        if (window.lucide?.createIcons) window.lucide.createIcons();
      },
      close() {
        el.classList.remove('zy-popover-open');
        el.style.display = 'none';
        trigger.setAttribute('aria-expanded', 'false');
      },
      toggle() {
        if (el.style.display === 'none') obj.open(); else obj.close();
      },
    };

    function position() {
      const r = trigger.getBoundingClientRect();
      const width = opts.width || 320;
      let left = r.right - width;
      let top = r.bottom + 10;
      if (opts.align === 'left') left = r.left;
      if (left < 8) left = 8;
      el.style.width = width + 'px';
      el.style.position = 'fixed';
      el.style.top = top + 'px';
      el.style.left = left + 'px';
      el.style.zIndex = 9999;
    }
    window.addEventListener('resize', () => { if (el.style.display !== 'none') position(); });
    window.addEventListener('scroll', () => { if (el.style.display !== 'none') position(); }, true);

    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      obj.toggle();
    });
    registry.add(obj);
    return obj;
  }

  /* ------------ ICON BUTTON ------------ */
  function buildIconButton({ icon, badge, label, attr }) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'zy-header-icon-btn group';
    btn.setAttribute('aria-label', label);
    if (attr) btn.setAttribute(attr, '');
    btn.innerHTML =
      `<i data-lucide="${icon}" class="size-5" aria-hidden="true"></i>` +
      (badge ? `<span class="zy-badge">${badge}</span>` : '');
    return btn;
  }

  /* ------------ POPOVER CONTENT ------------ */
  function messagesContent() {
    const items = [
      { who: 'Sophie L.',     msg: 'Peux-tu valider le devis #A-118 ?', when: '5 min' },
      { who: 'Thomas B.',     msg: 'Rapport hebdo prêt à relire.',      when: '23 min' },
    ];
    return `
      <div class="zy-pop-header">
        <p class="zy-pop-title">Messages</p>
        <p class="zy-pop-sub">${items.length} non lus</p>
      </div>
      <ul class="zy-pop-list">
        ${items.map((m) => `
          <li class="zy-pop-item">
            <div class="zy-pop-avatar">${m.who.split(' ').map((s) => s[0]).join('')}</div>
            <div class="zy-pop-body">
              <p class="zy-pop-name">${m.who}</p>
              <p class="zy-pop-line">${m.msg}</p>
            </div>
            <span class="zy-pop-time">${m.when}</span>
          </li>`).join('')}
      </ul>
      <a class="zy-pop-footer" href="copilote.html">Ouvrir la messagerie <i data-lucide="arrow-right" class="size-4"></i></a>
    `;
  }
  function mailContent() {
    const items = [
      { who: 'Comptable',        msg: 'Facture #2025-114 — 1 290 €',     when: '1 h' },
      { who: 'Expansion Agent',  msg: 'Nouveau lead chaud détecté (8/10)', when: '2 h' },
    ];
    return `
      <div class="zy-pop-header">
        <p class="zy-pop-title">Mail</p>
        <p class="zy-pop-sub">${items.length} non lus</p>
      </div>
      <ul class="zy-pop-list">
        ${items.map((m) => `
          <li class="zy-pop-item">
            <div class="zy-pop-avatar"><i data-lucide="mail" class="size-4"></i></div>
            <div class="zy-pop-body">
              <p class="zy-pop-name">${m.who}</p>
              <p class="zy-pop-line">${m.msg}</p>
            </div>
            <span class="zy-pop-time">${m.when}</span>
          </li>`).join('')}
      </ul>
      <a class="zy-pop-footer" href="expansion.html">Tout voir <i data-lucide="arrow-right" class="size-4"></i></a>
    `;
  }
  function bellContent() {
    const items = [
      { icon: 'heart-pulse', txt: 'Check-in énergie effectué — score 4/5', when: 'auj.' },
      { icon: 'target',      txt: '3 missions prêtes à être lancées',      when: '1 h' },
      { icon: 'wallet',      txt: 'Bridge a synchronisé ton CA du jour',  when: '3 h' },
    ];
    return `
      <div class="zy-pop-header">
        <p class="zy-pop-title">Notifications</p>
        <p class="zy-pop-sub">${items.length} nouvelles</p>
      </div>
      <ul class="zy-pop-list">
        ${items.map((m) => `
          <li class="zy-pop-item">
            <div class="zy-pop-icon-bubble"><i data-lucide="${m.icon}" class="size-4"></i></div>
            <div class="zy-pop-body"><p class="zy-pop-line">${m.txt}</p></div>
            <span class="zy-pop-time">${m.when}</span>
          </li>`).join('')}
      </ul>
      <a class="zy-pop-footer" href="index.html">Tout voir <i data-lucide="arrow-right" class="size-4"></i></a>
    `;
  }
  function profileContent() {
    return `
      <div class="zy-pop-profile-head">
        <p class="zy-pop-account">Account User</p>
        <p class="zy-pop-email">user@zayado.com</p>
      </div>
      <ul class="zy-pop-menu">
        <li><a href="settings.html" class="zy-pop-menu-item"><i data-lucide="user" class="size-4"></i><span>Profile</span></a></li>
        <li><a href="settings.html" class="zy-pop-menu-item"><i data-lucide="settings" class="size-4"></i><span>Settings</span></a></li>
        <li><a href="abonnement.html" class="zy-pop-menu-item"><i data-lucide="credit-card" class="size-4"></i><span>Billing &amp; Plans</span></a></li>
      </ul>
      <div class="zy-pop-divider"></div>
      <ul class="zy-pop-menu">
        <li><button type="button" class="zy-pop-menu-item zy-danger" data-zayado-logout><i data-lucide="log-out" class="size-4"></i><span>Log out</span></button></li>
      </ul>
    `;
  }

  /* ------------ ENHANCE HEADER ------------ */
  function enhanceHeader() {
    const header = document.querySelector('header.sticky');
    if (!header) return false;
    if (header.querySelector('[data-zayado-theme-toggle]')) return true;

    const bellWrapper = header.querySelector('[data-demo-bell]')?.closest('.dropdown');
    if (!bellWrapper) return false;

    // 1. Theme toggle
    const themeBtn = buildIconButton({ icon: 'moon', label: 'Toggle theme', attr: 'data-zayado-theme-toggle' });
    themeBtn.addEventListener('click', () => applyTheme(currentTheme() === 'dark' ? 'light' : 'dark'));

    // 2. Messages
    const chatBtn = buildIconButton({ icon: 'message-circle', badge: '2', label: 'Messages' });
    makePopover(chatBtn, messagesContent(), { width: 340 });

    // 3. Mail
    const mailBtn = buildIconButton({ icon: 'mail', badge: '2', label: 'Mail' });
    makePopover(mailBtn, mailContent(), { width: 340 });

    bellWrapper.parentNode.insertBefore(themeBtn, bellWrapper);
    bellWrapper.parentNode.insertBefore(chatBtn, bellWrapper);
    bellWrapper.parentNode.insertBefore(mailBtn, bellWrapper);

    // 4. Replace bell <details> with a custom popover button so it actually opens
    const existingBell = header.querySelector('[data-demo-bell]');
    if (existingBell) {
      const newBell = buildIconButton({ icon: 'bell', badge: '3', label: 'Notifications' });
      // The bell parent (.dropdown details) -> replace it
      const detailsParent = existingBell.closest('details, .dropdown');
      detailsParent.replaceWith(newBell);
      makePopover(newBell, bellContent(), { width: 360 });
    }

    // 5. Replace avatar dropdown with profile popover.
    // The avatar dropdown is .dropdown.dropdown-end.dropdown-bottom inside the header.
    // We must find it BEFORE lucide replaces <i data-lucide="circle-user"> with <svg>.
    let avatarDropdown =
      header.querySelector('.dropdown.dropdown-end.dropdown-bottom') ||
      header.querySelector('i[data-lucide="circle-user"]')?.closest('.dropdown') ||
      header.querySelector('svg.lucide-circle-user')?.closest('.dropdown');
    if (avatarDropdown) {
      const newAvatar = document.createElement('button');
      newAvatar.type = 'button';
      newAvatar.className = 'zy-header-avatar-btn';
      newAvatar.setAttribute('aria-label', 'Account');
      newAvatar.setAttribute('data-zayado-avatar', '');
      newAvatar.innerHTML = '';
      avatarDropdown.replaceWith(newAvatar);
      const pop = makePopover(newAvatar, profileContent(), { width: 280 });
      // Logout handler
      document.addEventListener('click', (e) => {
        if (e.target.closest('[data-zayado-logout]')) {
          pop.close();
          alert('D\u00e9connexion \u2014 (mockup)');
        }
      });
    }

    if (window.lucide?.createIcons) window.lucide.createIcons();
    updateToggleIcon();
    return true;
  }

  /* ------------ SIDEBAR : "..." more popover ------------ */
  function enhanceSidebar() {
    const moreBtn = document.querySelector('[data-zayado-more-btn]');
    if (!moreBtn || moreBtn.dataset.zayadoBound === '1') return false;
    moreBtn.dataset.zayadoBound = '1';

    const html = `
      <div class="zy-pop-header"><p class="zy-pop-title">Plus</p><p class="zy-pop-sub">Modules secondaires</p></div>
      <ul class="zy-pop-menu">
        <li><a href="thesustain.html" class="zy-pop-menu-item"><i data-lucide="leaf" class="size-4"></i><span>TheSustain</span></a></li>
        <li><a href="abonnement.html" class="zy-pop-menu-item"><i data-lucide="credit-card" class="size-4"></i><span>Abonnement</span></a></li>
      </ul>
    `;
    // Build popover that anchors to the right of the moreBtn (sidebar is left-side rail)
    const el = document.createElement('div');
    el.className = 'zy-popover';
    el.innerHTML = html;
    el.style.display = 'none';
    document.body.appendChild(el);

    const obj = {
      el,
      trigger: moreBtn,
      open() {
        closeAll(obj);
        const r = moreBtn.getBoundingClientRect();
        el.style.position = 'fixed';
        el.style.left = (r.right + 14) + 'px';
        el.style.top = (r.top - 6) + 'px';
        el.style.width = '240px';
        el.style.zIndex = 9999;
        el.style.display = 'block';
        requestAnimationFrame(() => el.classList.add('zy-popover-open'));
        moreBtn.setAttribute('aria-expanded', 'true');
        if (window.lucide?.createIcons) window.lucide.createIcons();
      },
      close() {
        el.classList.remove('zy-popover-open');
        el.style.display = 'none';
        moreBtn.setAttribute('aria-expanded', 'false');
      },
      toggle() { el.style.display === 'none' ? obj.open() : obj.close(); },
    };
    moreBtn.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); obj.toggle(); });
    registry.add(obj);
    return true;
  }

  /* ------------ BOOT ------------ */
  applyTheme(currentTheme());
  let tries = 0;
  const interval = setInterval(() => {
    tries += 1;
    const a = enhanceHeader();
    const b = enhanceSidebar();
    if ((a && b) || tries > 60) clearInterval(interval);
  }, 150);

  window.addEventListener('load', () => { enhanceHeader(); enhanceSidebar(); });
  document.addEventListener('DOMContentLoaded', () => { enhanceHeader(); enhanceSidebar(); });
})();
