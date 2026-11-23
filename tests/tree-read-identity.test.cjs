const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');
const html = fs.readFileSync(path.join(__dirname, '../board/index.html'), 'utf8');
const syncSource = fs.readFileSync(path.join(__dirname, '../board/tree-read-sync.js'), 'utf8');
const source = html.slice(html.indexOf('function treeVersion('), html.indexOf('function treeUpdateUnread('));
function context(nodes, versions = {}) {
  const ctx = vm.createContext({TREE_O: {tree: nodes}, treeReadVersions: versions,
    treeNodes: () => nodes.map(node => ({node}))});
  vm.runInContext(source, ctx);
  return ctx;
}
test('same-titled reports retain independent read states and renamed report stays read', () => {
  const a = {title: 'Result', page: 'reports/a.html', summary: 'a'};
  const b = {title: 'Result', page: 'reports/b.html', summary: 'b'};
  const ctx = context([a, b]);
  const key = ctx.treeReadKey(a);
  ctx.treeReadVersions[key] = ctx.treeVersion(a);
  assert.equal(ctx.treeIsUnread(a), false);
  assert.equal(ctx.treeIsUnread(b), true);
  a.title = 'Renamed result';
  assert.equal(ctx.treeIsUnread(a), false);
});
test('old metadata versions survive rebuild while visible new content becomes unread', () => {
  const node = {title: 'Old', page: 'reports/old.html', summary: 'Reviewed'};
  const ctx = context([node], {Old: JSON.stringify(['Reviewed', node.page, 12345, 120])});
  assert.equal(ctx.treeIsUnread(node), false);
  ctx.treeReadVersions[ctx.treeReadKey(node)] = ctx.treeVersion(node);
  node.summary = 'Revised';
  assert.equal(ctx.treeIsUnread(node), true);
});
test('ambiguous legacy title marker leaves same-titled nodes independently unread', () => {
  const a = {title:'Same',page:'a.html',summary:'same'};
  const b = {title:'Same',page:'b.html',summary:'same'};
  const ctx = context([a,b], {Same:JSON.stringify(['same','a.html',123,1])});
  assert.equal(ctx.treeIsUnread(a), true);
  assert.equal(ctx.treeIsUnread(b), true);
});
test('explicit unread survives legacy title fallback and persistence reload', () => {
  const node = {title:'Read',page:'read.html',summary:'read'};
  const ctx = context([node], {Read:JSON.stringify(['read','read.html',123,1])});
  ctx.treeReadVersions[ctx.treeReadKey(node)] = null;
  const reloaded = context([node], JSON.parse(JSON.stringify(ctx.treeReadVersions)));
  assert.equal(reloaded.treeIsUnread(node), true);
});
test('shared read script loads independently of private board closures', () => {
  const window = {};
  const ctx = vm.createContext({window});
  assert.doesNotThrow(() => vm.runInContext(syncSource, ctx));
  assert.equal(typeof window.BoardTreeReadSync.install, 'function');
  assert.equal(ctx.treeReadVersions, undefined);
  assert.equal(ctx.renderTree, undefined);
});

function synchronizedContext(nodes, {local = {}, server = {revision:0, versions:{}}} = {}) {
  const requests = [], renders = [], alerts = [];
  const ctx = vm.createContext({nodesInput:nodes, renders,
    localStorage:{getItem:() => JSON.stringify(local)},
    console, alert:message => alerts.push(message),
    fetch:async (url, options) => {
      const payload = JSON.parse(options.body);
      requests.push({url, payload});
      server = {revision:server.revision + 1, versions:{...server.versions,
        [payload.key]:payload.read ? payload.version : null}};
      return {ok:true, json:async () => server};
    }});
  ctx.window = ctx;
  vm.runInContext(syncSource, ctx);
  const start = html.indexOf('const treeReadSync = BoardTreeReadSync.install(');
  assert.ok(start >= 0, 'board installs the shared module inside its own closure');
  const wiring = html.slice(start, html.indexOf('load().then(spy)', start));
  vm.runInContext(`const client = (() => {
    let TREE_O = null, treeReadVersions = {};
    function treeNodes() { return nodesInput.map(node => ({node})); }
    ${source}
    function renderTree(o, force = false) {
      TREE_O = o;
      renders.push({force, unread:nodesInput.map(treeIsUnread)});
      return 'rendered';
    }
    function treeMarkRead() { throw new Error('local-only read handler'); }
    function treeMarkUnread() { throw new Error('local-only unread handler'); }
    ${wiring}
    return {render:(...args) => renderTree(...args),
      markRead:node => treeMarkRead(node), markUnread:node => treeMarkUnread(node),
      unread:treeIsUnread, key:treeReadKey, version:treeVersion};
  })();`, ctx);
  return {client:vm.runInContext('client', ctx), requests, renders, alerts, ctx};
}

test('board loads the module before its private async setup starts', () => {
  assert.ok(html.indexOf('<script src="/tree-read-sync.js"></script>')
    < html.indexOf('(async () => { await BoardIdentity.ready;'));
  assert.equal((html.match(/<script src="\/?tree-read-sync\.js"><\/script>/g) || []).length, 1);
});

test('private board render applies server read versions and ignores stale revisions', () => {
  const node = {id:'result', title:'Result', summary:'Reviewed'};
  const {client, renders, ctx} = synchronizedContext([node]);
  const versions = {[client.key(node)]:client.version(node)};
  assert.equal(client.render({tree:[node], tree_reads:{revision:2, versions}}), 'rendered');
  assert.equal(client.unread(node), false);
  assert.equal(renders.at(-1).force, true);
  client.render({tree:[node], tree_reads:{revision:1, versions:{}}});
  assert.equal(client.unread(node), false);
  assert.equal(ctx.treeReadVersions, undefined);
  assert.equal(ctx.renderTree, undefined);
});

test('read and unread clicks save through the shared endpoint then repaint private state', async () => {
  const node = {id:'result', title:'Result', summary:'Reviewed'};
  const {client, requests, renders, alerts} = synchronizedContext([node]);
  client.render({tree:[node], tree_reads:{revision:0, versions:{}}});
  await client.markRead(node);
  assert.equal(client.unread(node), false);
  await client.markUnread(node);
  assert.equal(client.unread(node), true);
  assert.deepEqual(requests.map(({url, payload}) => [url, payload.key, payload.read]),
    [['/api/tree/read', 'id:result', true], ['/api/tree/read', 'id:result', false]]);
  assert.equal(requests[0].payload.version, client.version(node));
  assert.equal(renders.at(-1).force, true);
  assert.deepEqual(alerts, []);
});

test('first server refresh migrates matching local markers once and preserves explicit unread', async () => {
  const a = {id:'a', title:'A', summary:'read locally'};
  const b = {id:'b', title:'B', summary:'read locally'};
  const identity = context([a, b]);
  const local = {'id:a':identity.treeVersion(a), 'id:b':identity.treeVersion(b)};
  const server = {revision:0, versions:{'id:b':null}};
  const {client, requests} = synchronizedContext([a, b], {local, server});
  const overview = {tree:[a, b], tree_reads:server};
  client.render(overview);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(client.unread(a), false);
  assert.equal(client.unread(b), true);
  assert.deepEqual(requests.map(row => row.payload.key), ['id:a']);
  client.render({tree:[a, b], tree_reads:{revision:1,
    versions:{'id:a':client.version(a), 'id:b':null}}});
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(requests.length, 1);
});
