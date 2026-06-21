/* ============================================================
   Vision Board interactions (mockup)
   - Tab switching (Vision Canvas / Strategic Pillars / Core Values)
   - State preview switch (1 / 2 / 3)
   - Edit panel toggle on user-block click
   ============================================================ */
(function () {
  'use strict';

  function init() {
    const root = document.querySelector('.zy-vb-root');
    if (!root || root.dataset.zybooted === '1') return false;
    const canvas = root.querySelector('.zy-vb-canvas');
    if (!canvas) return false;
    root.dataset.zybooted = '1';

    // Tabs (visual only for mockup)
    root.querySelectorAll('.zy-vb-tab').forEach((btn) => {
      btn.addEventListener('click', () => {
        root.querySelectorAll('.zy-vb-tab').forEach((b) => b.classList.remove('zy-vb-tab-active'));
        btn.classList.add('zy-vb-tab-active');
      });
    });

    // State preview switch
    root.querySelectorAll('.zy-vb-state-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        root.querySelectorAll('.zy-vb-state-btn').forEach((b) => b.classList.remove('zy-vb-state-active'));
        btn.classList.add('zy-vb-state-active');
        const state = btn.getAttribute('data-state');
        canvas.setAttribute('data-state', state);
      });
    });

    // Edit panel : open on click on a user block
    const editPanel = canvas.querySelector('.zy-vb-edit-panel');
    if (editPanel) {
      canvas.querySelectorAll('.zy-vb-block-user').forEach((bl) => {
        bl.addEventListener('click', (e) => {
          if (e.target.closest('.zy-vb-grip')) return;
          editPanel.classList.add('open');
        });
      });
      editPanel.querySelector('.zy-vb-edit-close')?.addEventListener('click', () => {
        editPanel.classList.remove('open');
      });
      editPanel.querySelectorAll('.zy-vb-edit-foot button').forEach((b) =>
        b.addEventListener('click', () => editPanel.classList.remove('open'))
      );
    }

    if (window.lucide?.createIcons) window.lucide.createIcons();
    return true;
  }

  let tries = 0;
  const iv = setInterval(() => {
    tries += 1;
    if (init() || tries > 60) clearInterval(iv);
  }, 150);
  document.addEventListener('DOMContentLoaded', init);
  window.addEventListener('load', init);
})();
