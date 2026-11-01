(() => {
  if (!window.matchMedia || matchMedia('(prefers-reduced-motion: reduce)').matches) return;


  document.addEventListener('click', event => {
    const summary = event.target.closest?.('summary');
    const box = summary?.parentElement;
    if (!box || box.tagName !== 'DETAILS' || box.open || summary.closest('#msgs, dialog')) return;
    if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.shiftKey) return;
    const closed = box.getBoundingClientRect().height;
    setTimeout(() => {
      if (!box.open || !box.isConnected) return;
      const open = box.getBoundingClientRect().height;
      if (open - closed < 4) return;
      box.animate([{height: closed + 'px', overflow: 'clip'}, {height: open + 'px', overflow: 'clip'}],
        {duration: Math.min(420, 180 + (open - closed) * 0.25), easing: 'cubic-bezier(.22,1,.36,1)'});
      [...box.children].filter(c => c !== summary).forEach(c => c.animate([{opacity: 0, translate: '0 -6px'}, {opacity: 1, translate: '0 0'}],
        {duration: 300, delay: 40, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards'}));
    }, 0);
  }, true);

  const wrapTheme = () => document.querySelectorAll('.theme-switch button').forEach(b => {
    if (b.dataset.moWrapped || typeof b.onclick !== 'function') return;
    const original = b.onclick; b.dataset.moWrapped = '1';
    b.onclick = event => {
      if (!document.startViewTransition) return original.call(b, event);
      document.startViewTransition(() => original.call(b, event));

      setTimeout(() => { if (document.documentElement.className !== 'theme-' + b.dataset.t) original.call(b, event); }, 600);
    };
  });
  wrapTheme();

  const body = document.getElementById('task-body');
  if (body) {
    let last = null;
    const snapshot = () => {
      const now = new Map();
      body.querySelectorAll('.task').forEach(task => {
        const name = task.querySelector('.n')?.textContent.trim(); if (!name) return;
        now.set(name, (task.querySelector('.task-labels')?.textContent || '') + '|' + (task.querySelector('.eta,.task-eta,.tt-bar')?.textContent || ''));
      });
      if (last) body.querySelectorAll('.task').forEach(task => {
        const name = task.querySelector('.n')?.textContent.trim();
        if (name && last.has(name) && last.get(name) !== now.get(name)) {
          task.classList.remove('mo-changed'); void task.offsetWidth; task.classList.add('mo-changed');
          setTimeout(() => task.classList.remove('mo-changed'), 1700);
        }
      });
      last = now;
    };
    let pending = 0;
    new MutationObserver(() => { cancelAnimationFrame(pending); pending = requestAnimationFrame(snapshot); }).observe(body, {childList: true, subtree: true});
    snapshot();
  }
})();
