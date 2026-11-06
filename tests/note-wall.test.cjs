const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('wall stays within its width, preserves stable positions and separates cards',()=>{
 for(const width of [290,700,1300]){
  const cards=Array.from({length:8},(_,i)=>({classList:{contains:()=>true},dataset:{wallText:'A'.repeat(20+i*20)},textContent:'Note',style:{setProperty(k,v){this[k]=v;},removeProperty(){}},offsetHeight:90+i*10}));
  const classes=new Set(),list={clientWidth:width,children:cards,style:{},classList:{contains:k=>classes.has(k),add:k=>classes.add(k),remove:k=>classes.delete(k)}};
  const root={matches:()=>true,classList:{contains:()=>true}};
  const context={window:{},document:{getElementById:()=>list,documentElement:root},getComputedStyle:()=>({paddingLeft:'4',paddingRight:'4'}),MutationObserver:class{observe(){}},ResizeObserver:class{observe(){}},setTimeout:()=>0,clearTimeout(){},addEventListener(){}};
  let source=fs.readFileSync('board/notebook.js','utf8').replace('  later();','  window.layout=layout;');
  vm.runInNewContext(source,context);context.window.layout();
  const boxes=()=>cards.map(c=>({x:parseFloat(c.style.left),y:parseFloat(c.style.top),w:parseFloat(c.style.width),h:c.offsetHeight,color:c.dataset.c}));
  const first=boxes();context.window.layout();assert.deepEqual(boxes(),first);
  for(const box of first){assert.ok(box.x>=0);assert.ok(box.x+box.w<=width);}
  for(let i=0;i<first.length;i++)for(let j=i+1;j<first.length;j++){
   const a=first[i],b=first[j];assert.ok(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y);
  }
 }
});

test('container width changes relayout the wall while height changes stay quiet',()=>{
 const cards=Array.from({length:8},(_,i)=>({classList:{contains:()=>true},dataset:{wallText:'A'.repeat(30+i*20)},textContent:'Note',style:{setProperty(k,v){this[k]=v;},removeProperty(){}},offsetHeight:100}));
 const classes=new Set(),list={clientWidth:700,children:cards,style:{},classList:{contains:k=>classes.has(k),add:k=>classes.add(k),remove:k=>classes.delete(k)}};
 const root={matches:()=>true,classList:{contains:()=>true}},timers=new Map();let tick=0,resize;
 const flush=()=>{while(timers.size){const batch=[...timers.values()];timers.clear();for(const fn of batch)fn();}};
 const context={window:{},document:{getElementById:()=>list,documentElement:root},getComputedStyle:()=>({paddingLeft:'4',paddingRight:'4'}),MutationObserver:class{observe(){}},ResizeObserver:class{constructor(fn){resize=fn;}observe(el){assert.equal(el,list);}},setTimeout(fn){timers.set(++tick,fn);return tick;},clearTimeout(id){timers.delete(id);},addEventListener(){}};
 vm.runInNewContext(fs.readFileSync('board/notebook.js','utf8'),context);flush();
 const first=cards.map(c=>c.style.left);resize();assert.equal(timers.size,0);
 list.style.height='1200px';resize();assert.equal(timers.size,0);
 list.clientWidth=290;resize();assert.equal(timers.size,1);resize();assert.equal(timers.size,1);flush();
 assert.notDeepEqual(cards.map(c=>c.style.left),first);
 for(const card of cards)assert.ok(parseFloat(card.style.left)+parseFloat(card.style.width)<=290);
 resize();assert.equal(timers.size,0);
});
