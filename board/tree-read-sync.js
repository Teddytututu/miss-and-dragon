/* Shared markers reuse the board refresh and retain the existing tree layout. */
(() => {
  'use strict';
  function install({render:originalRender, getOverview, getVersions, setVersions,
                    nodes, savedVersion, version, key, matches}) {
    let revision = -1;
    let writes = Promise.resolve();
    function apply(state) {
      if (!state || !Number.isInteger(state.revision) || state.revision < revision) return false;
      const changed = JSON.stringify(getVersions()) !== JSON.stringify(state.versions || {});
      revision = state.revision;
      setVersions({...state.versions});
      return changed;
    }
    // Merge historical browser markers on the first server refresh.
    let merged = false;
    function mergeLocal(o) {
      if (merged || !o?.tree_reads) return; merged = true;
      let local = {}; try { local = JSON.parse(localStorage.getItem('result-tree-read-v1') || '{}') || {}; } catch (_) {}
      const server = o.tree_reads.versions || {};
      for (const row of nodes()) {
        if (savedVersion(row.node, server) === undefined && matches(savedVersion(row.node, local), version(row.node))) mark(row.node, true);
      }
    }
    function render(o, force = false) {
      const changed = apply(o.tree_reads);
      const out = originalRender(o, force || changed);
      try { mergeLocal(o); } catch (e) { console.warn('tree read merge', e); }
      return out;
    }
    function mark(node, read) {
      const payload = {title:node.title, key:key(node), version:version(node), read};
      writes = writes.catch(() => {}).then(async () => {
        const response = await fetch('/api/tree/read', {
          method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
        });
        const state = await response.json();
        if (!response.ok) throw new Error(state.error || '已读状态保存失败');
        apply(state);
        const overview = getOverview();
        if (overview) originalRender(overview, true);
      }).catch(error => { console.error(error); alert('已读状态保存遇到问题，请重试。'); });
      return writes;
    }
    setVersions({});
    const overview = getOverview();
    if (overview) render(overview, true);
    return {render, markRead:node => mark(node, true), markUnread:node => mark(node, false)};
  }
  window.BoardTreeReadSync = {install};
})();
