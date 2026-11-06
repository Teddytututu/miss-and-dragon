const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function tree(){
 const html=fs.readFileSync('board/index.html','utf8');
 const source=html.slice(html.indexOf('let TREE_O = null;'),html.indexOf('function taskState'));
 const context={document:{addEventListener(){},querySelectorAll(){return []},querySelector(){return null}},localStorage:{getItem(){return null},setItem(){}},collapsed:new Map()};
 vm.runInNewContext(source+`;this.api={nodes:treeNodes,chain:treeChainTitles,version:treeVersion,unread:treeIsUnread,read:treeMarkRead,set(o){TREE_O=o}}`,context);return context.api;
}
test('causal chain follows directions without crossing into sibling branches',()=>{
 const api=tree();api.set({tree:[{title:'Root',to:['A','B'],children:[{title:'A',from:['Root'],to:['C']},{title:'B',from:['Root']},{title:'C',from:['A']}]}]});
 assert.deepEqual([...api.chain('A')].sort(),['A','C','Root']);assert.equal(api.nodes().length,4);
});
test('read versions follow summaries and report metadata',()=>{
 const api=tree(),node={title:'A',summary:'Ready',page:'report.html'},data={tree:[node],links:[{path:'report.html',mtime_ns:10,size:20}]};api.set(data);
 assert.equal(api.unread(node),true);api.read(node);assert.equal(api.unread(node),false);
 data.links[0].mtime_ns=11;assert.equal(api.unread(node),true);api.read(node);node.summary='Updated';assert.equal(api.unread(node),true);
});
