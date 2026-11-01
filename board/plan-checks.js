/* One task control shared by the private notebook and the project board. */
(() => {
  'use strict';
  const pending = new Map();
  function dates(label, reference=new Date()) {
    const year=reference.getFullYear();
    return (String(label).match(/(?:\d{4}-)?\d{2}-\d{2}/g)||[]).map(value=>{
      if(value.length===10)return value;
      return [year-1,year,year+1].map(y=>y+'-'+value).sort((a,b)=>
        Math.abs(new Date(a+'T12:00:00')-reference)-Math.abs(new Date(b+'T12:00:00')-reference))[0];
    });
  }
  const make = (tag, cls) => { const node=document.createElement(tag); if(cls)node.className=cls; return node; };
  const labelInput = input => input.setAttribute('aria-label',
    (window.BoardI18n?.language==='en'?'Completed: ':'完成：')+input.closest('label').querySelector('.plan-check-text').textContent);
  function paint(row, completed, saving, message='') {
    row.classList.toggle('plan-done',completed);
    row.classList.toggle('plan-saving',saving);
    const input=row.querySelector('.plan-check-input');
    input.checked=completed; input.disabled=saving;
    row.querySelector('.plan-check-label').setAttribute('aria-busy',String(saving));
    row.querySelector('.plan-check-status').textContent=message;
  }
  function paintCurrent(id, completed, saving, message) {
    document.querySelectorAll('.slot[data-plan-id]').forEach(row=>{
      if(row.dataset.planId===id)paint(row,completed,saving,message);
    });
  }
  function attach(row,item) {
    if(!item.check_id)return;
    row.dataset.planId=item.check_id;
    const host=row.querySelector('.w'), label=make('label','plan-check-label');
    const input=make('input','plan-check-input'), text=make('span','plan-check-text');
    input.type='checkbox'; text.textContent=item.what;
    const status=make('span','plan-check-status');status.setAttribute('role','status');
    label.append(input,text);host.replaceChildren(label,status);
    labelInput(input);
    const waiting=pending.get(item.check_id);
    paint(row,waiting?.completed??item.completed===true,Boolean(waiting));
    input.addEventListener('change',async()=>{
      const restoreFocus=document.activeElement===input;
      const previous=item.completed===true, completed=input.checked;
      pending.set(item.check_id,{completed});paintCurrent(item.check_id,completed,true,'');
      try {
        const response=await fetch('/api/plan/check',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({id:item.check_id,completed})});
        const result=await response.json();
        if(!response.ok)throw new Error(result.error||'请重试保存。');
        item.completed=result.completed;
        paintCurrent(item.check_id,result.completed,false,'');
      } catch(error) {
        paintCurrent(item.check_id,previous,false,error.message||'请重试保存。');
      } finally {
        pending.delete(item.check_id);
        if(restoreFocus && (document.activeElement===document.body || document.activeElement===input)) {
          const current=Array.from(document.querySelectorAll('.slot[data-plan-id]')).find(r=>r.dataset.planId===item.check_id);
          current?.querySelector('input')?.focus({preventScroll:true});
        }
      }
    });
  }
  window.PlanChecks={attach,dates};
  window.addEventListener('languagechange',()=>document.querySelectorAll('.plan-check-input').forEach(labelInput));
})();
