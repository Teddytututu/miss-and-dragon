/* Content-sized paper notes share one stable wall across both themes. */
(() => {
  const list = document.getElementById('todo-list');
  if (!list) return;
  const hash = text => { let h = 2166136261; for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };
  const rand = (seed, k) => ((Math.imul(seed ^ (k * 0x9e3779b1), 2654435761) >>> 0) % 1000) / 1000;
  let busy = false;
  const layout = () => {
    const items = [...list.children].filter(e => e.classList.contains('todo-item'));
    const paperTheme = document.documentElement.matches('.theme-pink, .theme-default');
    if (!paperTheme || !items.length) {
      if (list.classList.contains('wall')) { list.classList.remove('wall'); list.style.height = ''; items.forEach(e => { e.style.left = e.style.top = e.style.width = ''; e.style.removeProperty('--wall-rot'); }); }
      return;
    }
    if (list.clientWidth < 32) return;
    busy = true;
    list.classList.add('wall');
    const cs = getComputedStyle(list);
    const padL = parseFloat(cs.paddingLeft) + 6, padR = parseFloat(cs.paddingRight) + 6;
    const width = list.clientWidth - padL - padR;


    const W = Math.floor(width), gapY = 18, gapX = 22;
    const top = 16;
    const sky = new Array(W).fill(top);
    const single = W < 460, base = W >= 700 ? 232 : 210;
    const placed = [];
    items.forEach((item, i) => {
      const text = (item.dataset.wallText || item.textContent).replace(/\s+/g, '');
      const seed = hash(text), len = text.length;
      let w;
      if (single) w = W * (len < 50 ? 0.84 : len < 110 ? 0.9 : 0.96);
      else w = base * (len < 40 ? 0.72 : len < 90 ? 0.9 : len < 150 ? 1.1 : 1.3) * (0.9 + rand(seed, 4) * 0.2);
      w = Math.round(Math.min(w, single ? W : W * 0.5));
      item.style.width = w + 'px';
      const h = item.offsetHeight;
      const deg = (i % 2 ? 1 : -1) * (0.6 + rand(seed, 3) * (single ? 1.6 : 2.9));
      const tilt = Math.ceil(w * Math.sin(Math.abs(deg) * Math.PI / 180) / 2);
      let bestX = 0, bestY = Infinity, bestScore = Infinity;

      const cands = new Set();
      for (let k = 0; k < W; ) {
        let e = k; while (e < W && sky[e] === sky[k]) e++;
        const jl = single ? Math.round(rand(seed, 21 + k) * (W - w)) : Math.round(rand(seed, 21 + k) * 14);
        cands.add(Math.min(W - w, k ? k + gapX + jl : 0));
        cands.add(Math.max(0, (e < W ? e - gapX : W) - w - Math.round(rand(seed, 31 + e) * 14)));
        k = e;
      }
      for (const x of cands) {
        if (x < 0 || x + w > W) continue;
        let y = 0;
        for (let k = Math.max(0, x - gapX); k < Math.min(W, x + w + gapX); k++) if (sky[k] > y) y = sky[k];
        const score = y + rand(seed, 11 + x) * (single ? 4 : 8) + x * 0.03;
        if (score < bestScore) { bestScore = score; bestX = x; bestY = y; }
      }
      const y = bestY + (bestY > top ? gapY : 0) + Math.round(rand(seed, 2) * 12);
      const x = padL + bestX;
      item.style.left = Math.round(x) + 'px';
      item.style.top = Math.round(y + tilt) + 'px';
      item.style.setProperty('--wall-rot', deg.toFixed(2) + 'deg');
      for (let k = bestX; k < bestX + w; k++) sky[k] = y + h + tilt * 2;
      const box = {x, y: y + tilt, w, h};
      const near = placed.filter(o => o.x < box.x + box.w + 40 && box.x < o.x + o.w + 40 && o.y < box.y + box.h + 40 && box.y < o.y + o.h + 40).map(o => o.c);
      let color = seed % 3; for (let t = 0; t < 3 && near.includes(color); t++) color = (color + 1) % 3;
      if (item.dataset.c !== String(color)) item.dataset.c = String(color);
      const colors = document.documentElement.classList.contains('theme-pink') ? ['#fff7df','#fff0f5','#eaf3ff'] : ['#eaf3ff','#fff7df','#eef5ef'];
      item.style.setProperty('--note-paper', colors[color]);
      placed.push({...box, c: color});
    });
    list.style.height = Math.round(Math.max(...sky) + 14) + 'px';
    setTimeout(() => { busy = false; }, 0);
  };
  let pending = 0;
  const later = () => { clearTimeout(pending); pending = setTimeout(layout, 40); };

  new MutationObserver(() => { if (!busy) { clearTimeout(pending); layout(); } }).observe(list, {childList: true, subtree: true, characterData: true});
  new MutationObserver(later).observe(document.documentElement, {attributes: true, attributeFilter: ['class']});
  addEventListener('resize', later);
  document.fonts?.ready.then(later);
  later();
})();
