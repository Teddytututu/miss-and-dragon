const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
test('drawer clamps width, supports keyboard/reset and restores desktop preference',()=>{
 const events={},attrs={},values={},saved={};
 const handle={addEventListener:(name,fn)=>events[name]=fn,setAttribute:(k,v)=>attrs[k]=v,focus(){},setPointerCapture(){}};
 const drawer={style:{setProperty:(k,v)=>values[k]=v}};
 const win={innerWidth:1000,addEventListener:(k,v)=>events['window:'+k]=v};
 const context={window:win,document:{getElementById:id=>id==='drawer'?drawer:handle,body:{classList:{add(){},remove(){}}}},localStorage:{getItem:()=>600,setItem:(k,v)=>saved[k]=v}};
 const html=fs.readFileSync('board/index.html','utf8'),source=html.split('<script id="result-drawer-width-control">')[1].split('</script>')[0];vm.runInNewContext(source,context);
 assert.equal(values['--result-drawer-width'],'600px');events.keydown({key:'End',preventDefault(){}});assert.equal(attrs['aria-valuenow'],800);
 win.innerWidth=375;events['window:resize']();assert.equal(attrs['aria-valuenow'],375);
 win.innerWidth=1000;events['window:resize']();assert.equal(attrs['aria-valuenow'],800);
 events.dblclick();assert.equal(attrs['aria-valuenow'],460);assert.equal(saved['result-drawer-width-v1'],'460');
 events.keydown({key:'Home',preventDefault(){}});assert.equal(attrs['aria-valuenow'],320);
});
