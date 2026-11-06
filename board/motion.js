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

/* Drag decorative stickers on their own composited layers. */
(() => {
  const SPOTS = [['#todo .todo-item:first-child', '::after', 'fish'], ['.hero', '::before', 'hero'], ['#lines.card', '::after', 'lines'], ['#task-body.card', '::after', 'task'], ['#files .card.fgrid', '::after', 'files']];
  const px = v => parseFloat(v) || 0;
  const geom = (host, pseudo) => {
    const cs = getComputedStyle(host, pseudo);
    if (cs.content === 'none' || cs.display === 'none') return null;
    const w = px(cs.width), h = px(cs.height), W = host.clientWidth;
    const x = cs.left !== 'auto' ? px(cs.left) + px(cs.marginLeft) : W - px(cs.right) - w;
    return {x, y: px(cs.top) + px(cs.marginTop), w, h, W, cs};
  };
  const bounds = g => {
    const lo = Math.min(8, Math.max(0, (g.W - g.w) / 2)) - g.x;
    return [lo, Math.max(lo, g.W - g.w - 8 - g.x)];
  };
  const copyLook = (inner, cs) => {
    for (const k of ['backgroundImage', 'backgroundSize', 'backgroundPosition', 'backgroundRepeat', 'transformOrigin', 'animationName', 'animationDuration', 'animationTimingFunction', 'animationIterationCount', 'animationDelay', 'zIndex'])
      inner.style[k] = cs[k];
  };
  const spots = [];
  let t = 0; const later = () => { clearTimeout(t); t = setTimeout(setup, 30); };
  const setup = () => {
    const pink = document.documentElement.classList.contains('theme-pink');
    for (const [sel, pseudo, key] of SPOTS) {
      const host = document.querySelector(sel);
      let sp = spots.find(s => s.key === key);
      if (sp && (!pink || sp.host !== host)) { sp.observer.disconnect(); sp.el.remove(); sp.host && sp.host.classList.remove('mo-real-' + (pseudo === '::after' ? 'a' : 'b')); spots.splice(spots.indexOf(sp), 1); sp = null; }
      if (!pink || !host) continue;
      const cls = 'mo-real-' + (pseudo === '::after' ? 'a' : 'b');
      const g = geom(host, pseudo);
      if (!g || g.w < 20) continue;
      if (!sp) {
        const el = document.createElement('div'), inner = document.createElement('div');
        el.className = 'mo-stk'; el.title = '拖着左右挪 · 双击回原位'; el.setAttribute('aria-hidden', 'true'); inner.className = 'mo-stk-in'; el.append(inner);
        if (getComputedStyle(host).position === 'static') host.style.position = 'relative';
        host.append(el);
        sp = {key, host, el, inner, cur: 0, dragging: false}; spots.push(sp);
        sp.observer = new MutationObserver(() => { if (el.parentElement !== host || !host.classList.contains(cls)) later(); });
        sp.observer.observe(host, {childList: true, attributes: true, attributeFilter: ['class']});
        let saved = 0; try { saved = +localStorage.getItem('mo-drag-' + key) || 0; } catch (_) {}
        sp.cur = saved;
        let start = 0, base = 0, lastX = 0, raf = 0, tilt = 0, pointer = null, lim = [0, 0];
        const band = v => v < lim[0] ? lim[0] - Math.sqrt(lim[0] - v) * 4 : v > lim[1] ? lim[1] + Math.sqrt(v - lim[1]) * 4 : v;
        const paint = () => { raf = 0; el.style.transform = `translate3d(${sp.cur}px,0,0) rotate(${tilt}deg)`; };
        el.addEventListener('pointerdown', e => {
          if (e.button || sp.dragging) return; e.preventDefault(); pointer = e.pointerId; el.setPointerCapture(pointer);
          sp.dragging = true; start = lastX = e.clientX; base = sp.cur; lim = bounds(sp.g);
          el.classList.add('mo-grab');
        });
        el.addEventListener('pointermove', e => {
          if (!sp.dragging || e.pointerId !== pointer) return;
          sp.cur = band(base + e.clientX - start);
          tilt = Math.max(-8, Math.min(8, (e.clientX - lastX) * 1.5)); lastX = e.clientX;
          if (!raf) raf = requestAnimationFrame(paint);
        });
        const end = e => {
          if (!sp.dragging || e.pointerId !== pointer) return;
          sp.dragging = false; cancelAnimationFrame(raf);
          if (el.hasPointerCapture(pointer)) el.releasePointerCapture(pointer);
          pointer = null; el.classList.remove('mo-grab');
          sp.cur = Math.max(lim[0], Math.min(lim[1], sp.cur)); tilt = 0; paint();
          try { localStorage.setItem('mo-drag-' + key, String(Math.round(sp.cur))); } catch (_) {}
        };
        el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end); el.addEventListener('lostpointercapture', end);
        el.addEventListener('dblclick', () => { sp.cur = 0; tilt = 0; paint(); try { localStorage.removeItem('mo-drag-' + key); } catch (_) {} });
      }
      if (sp.el.parentElement !== host) host.append(sp.el);   // Restore the layer after card rendering.
      if (sp.dragging) continue;
      sp.g = g;
      const [lo, hi] = bounds(g);
      sp.cur = Math.max(lo, Math.min(hi, sp.cur));
      Object.assign(sp.el.style, {left: g.x + 'px', top: g.y + 'px', width: g.w + 'px', height: g.h + 'px', transform: `translate3d(${sp.cur}px,0,0)`});
      copyLook(sp.inner, g.cs);
      if (!host.classList.contains(cls)) host.classList.add(cls);   // Hidden pseudo-elements keep their measurable geometry.
    }
  };
  
  addEventListener('resize', later); setTimeout(setup, 800); setInterval(() => { if (!spots.some(s => s.dragging)) setup(); }, 1500);
  new MutationObserver(later).observe(document.documentElement, {attributes: true, attributeFilter: ['class']});
})();
