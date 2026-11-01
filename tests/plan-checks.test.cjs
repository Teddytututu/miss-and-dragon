const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const context={window:{addEventListener(){}},Date};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../board/plan-checks.js'),'utf8'),context);
const dates=(text,ref)=>Array.from(context.window.PlanChecks.dates(text,new Date(ref)));
test('full dates and short ranges resolve to the displayed calendar day',()=>{
  assert.deepEqual(dates('2026-11-01','2026-11-01T08:00:00'),['2026-11-01']);
  assert.deepEqual(dates('11-01 至 11-03','2026-11-01T08:00:00'),['2026-11-01','2026-11-03']);
});
test('year boundary preserves upcoming January and recent December',()=>{
  assert.deepEqual(dates('01-01','2026-12-31T08:00:00'),['2027-01-01']);
  assert.deepEqual(dates('12-31','2027-01-01T08:00:00'),['2026-12-31']);
});
