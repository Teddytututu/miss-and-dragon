const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
class Element {
  constructor() {
    this.names = new Set(); this.style = {}; this.handlers = {}; this.children = []; this.clientWidth = 300;
    this.classList = {contains: n => this.names.has(n), add: n => this.names.add(n), remove: n => this.names.delete(n)};
  }
  set className(s) { this.names = new Set(s.split(' ')); }
  append(el) { el.remove(); this.children.push(el); el.parentElement = this; }
  remove() { if (this.parentElement) this.parentElement.children = this.parentElement.children.filter(x => x !== this); this.parentElement = null; }
  setAttribute() {}
  addEventListener(type, fn) { this.handlers[type] = fn; }
  setPointerCapture(id) { this.capture = id; }
  hasPointerCapture(id) { return this.capture === id; }
  releasePointerCapture() { this.capture = null; }
  fire(type, x = 0, id = 1) { this.handlers[type]({clientX: x, pointerId: id, button: 0, preventDefault() {}}); }
}
const root = new Element(); root.classList.add('theme-pink');
const selectors = ['#todo .todo-item:first-child', '.hero', '#lines.card', '#task-body.card', '#files .card.fgrid'];
const hosts = new Map(selectors.map(s => [s, new Element()]));
const timers = [], intervals = [], observers = [], frames = new Map(), values = new Map();
let sequence = 0;
const sandbox = {
  window: {matchMedia: () => ({matches: true})}, matchMedia: () => ({matches: true}),
  document: {documentElement: root, querySelector: s => hosts.get(s), createElement: () => new Element()},
  getComputedStyle: (el, pseudo) => pseudo ? {content: '""', display: 'block', width: '80px', height: '80px', left: 'auto', right: '10px', top: '-72px', marginTop: '0px', backgroundImage: 'url(original.png)', animationName: 'mo-breathe'} : {position: 'static'},
  MutationObserver: class {constructor(fn) {this.fn = fn; observers.push(this);} observe(host) {this.host = host;} disconnect() {this.disconnected = true;}},
  setTimeout: fn => {timers.push(fn); return timers.length;}, clearTimeout() {}, setInterval: fn => intervals.push(fn), addEventListener() {},
  requestAnimationFrame: fn => {frames.set(++sequence, fn); return sequence;}, cancelAnimationFrame: id => frames.delete(id),
  localStorage: {getItem: k => values.get(k), setItem: (k,v) => values.set(k,v), removeItem: k => values.delete(k)}
};
vm.runInNewContext(fs.readFileSync('board/motion.js', 'utf8'), sandbox);
timers.shift()();
const host = hosts.get(selectors[0]);
let el = host.children[0];
assert.equal(selectors.filter(s => hosts.get(s).children.length === 1).length, 5);
assert.equal(el.children[0].style.backgroundImage, 'url(original.png)');
assert.equal(el.children[0].style.animationName, 'mo-breathe');
const flush = () => {for (const [id, fn] of frames) {frames.delete(id); fn();}};
el.fire('pointerdown', 100); el.fire('pointermove', 120);
assert.equal(frames.size, 1); el.fire('pointermove', 125); assert.equal(frames.size, 1);
flush(); assert.match(el.style.transform, /rotate\(7.5deg\)/);
el.fire('pointerup', 125); assert.equal(values.get('mo-drag-fish'), '2');
assert.equal(el.style.transform, 'translate3d(2px,0,0) rotate(0deg)');
el.fire('pointerdown', 100); el.fire('pointermove', -900); flush();
assert.ok(parseFloat(el.style.transform.match(/\((-?[\d.]+)/)[1]) < -202);
el.fire('pointercancel', -900); assert.equal(values.get('mo-drag-fish'), '-202');
el.fire('dblclick'); assert.equal(values.has('mo-drag-fish'), false);
assert.equal(el.style.transform, 'translate3d(0px,0,0) rotate(0deg)');
el.fire('pointerdown', 100); el.fire('pointermove', 80, 2); assert.equal(frames.size, 0);
el.fire('lostpointercapture', 100); assert.equal(el.classList.contains('mo-grab'), false);
el.remove(); intervals[0](); assert.equal(host.children[0], el);
const priorObserver = observers.find(o => o.host === host);
const replacement = new Element(); hosts.set(selectors[0], replacement); values.set('mo-drag-fish', '-50'); intervals[0]();
assert.ok(priorObserver.disconnected); assert.equal(host.children.length, 0);
el = replacement.children[0]; assert.match(el.style.transform, /translate3d\(-50px/);
root.classList.remove('theme-pink'); intervals[0]();
assert.equal(replacement.children.length, 0); assert.equal(replacement.classList.contains('mo-real-a'), false);
root.classList.add('theme-pink'); replacement.clientWidth = 60; intervals[0]();
el = replacement.children[0]; el.fire('pointerdown', 0); el.fire('pointermove', 500); el.fire('pointerup', 500);
assert.equal(el.style.transform, 'translate3d(30px,0,0) rotate(0deg)');
console.log('Sticker drag: bounds, persistence, redraw, theme, reduced motion and pointer lifecycle passed');
