const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('history targets expand around the message, with a bounded automatic unread jump', () => {
  const log = {children:[], scrollTop:0, scrollHeight:500, clientHeight:100};
  const latest = {};
  const context = {window:{}, document:{querySelector:s=>s==='#room-threads'?log:latest}, RoomExtras:{visible:()=>true}, rendered:[]};
  let source = fs.readFileSync('board/discussion.js', 'utf8');
  source = source.replace('function render(options = {}) {', 'function render(options = {}) { rendered.push(options); } function unusedRender(options = {}) {');
  source = source.replace('return {init,update,cleanText,jumpTo,sizing};', 'return {jumpTo,set(rows){items=rows;limit=18;},limit:()=>limit};');
  vm.runInNewContext(source, context);
  const room = context.window.DiscussionRoom;
  const rows = Array.from({length:300}, (_,i)=>({id:String(i)}));
  room.set(rows); room.jumpTo('290', true);
  assert.equal(room.limit(),18);
  room.jumpTo('200', true);
  assert.equal(room.limit(),106);
  assert.equal(context.rendered.at(-1).auto,true);
  room.set(rows); room.jumpTo('0', true);
  assert.equal(room.limit(),18);
  assert.equal(log.scrollTop,500);
  room.jumpTo('0'); assert.equal(room.limit(),306);
  room.set(rows); room.jumpTo('missing'); assert.equal(room.limit(),18);
});
