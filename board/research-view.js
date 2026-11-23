/* Optional research views reuse the board's paper, themes and overview event. */
(() => {
  const en = () => document.documentElement.lang.startsWith('en');
  const t = (zh, english) => en() ? english : zh;
  const el = (tag, text, cls) => { const n = document.createElement(tag); if(text!=null)n.textContent=text;if(cls)n.className=cls;return n; };
  const tasks = document.getElementById('tasks');
  if (!tasks) return;
  const fold=el('details');fold.id='resource-fold';
  fold.append(el('summary',t('时间表','Timeline')));
  const toolbar=el('div',null,'resource-toolbar'), summary=el('span');
  const viewport=el('div',null,'resource-viewport');viewport.tabIndex=0;viewport.setAttribute('aria-label',t('资源时间表，左右拖动，Ctrl加滚轮缩放','Resource timeline: drag horizontally; Ctrl + wheel to zoom'));
  const grid=el('div',null,'resource-grid');viewport.append(grid);
  const tool=(text,fn)=>{const b=el('button',text);b.type='button';b.addEventListener('click',fn);toolbar.append(b);return b;};
  let pph=Number(localStorage.getItem('resource-pph'))||70, plan=null, signature='', manual=localStorage.getItem('resource-scroll')!==null, origin=0;
  const nameWidth=()=>matchMedia('(max-width:640px)').matches?92:168;
  const date=x=>new Date(x).toLocaleString(en()?'en-GB':'zh-TW',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
  function zoom(value,anchor=viewport.clientWidth/2){const old=pph;pph=Math.max(15,Math.min(280,value));const target=(viewport.scrollLeft+anchor-nameWidth())/old*pph+nameWidth()-anchor;draw();viewport.scrollLeft=target;manual=true;localStorage.setItem('resource-pph',String(pph));}
  tool('−',()=>zoom(pph/1.25));tool('+',()=>zoom(pph*1.25));
  const center=()=>{if(plan&&viewport.clientWidth)viewport.scrollLeft=nameWidth()+(new Date(plan.now)-origin)/3600000*pph-viewport.clientWidth/2;};
  tool(t('现在','Now'),()=>{manual=false;center();});
  tool(t('全屏','Full screen'),()=>document.fullscreenElement?document.exitFullscreen():fold.requestFullscreen?.());
  toolbar.append(summary);fold.append(toolbar,viewport);tasks.insertBefore(fold,tasks.querySelector('#task-body'));
  fold.hidden=true;fold.open=localStorage.getItem('resource-open')==='true';
  const issues=el('p');issues.setAttribute('role','status');issues.hidden=true;fold.after(issues);
  fold.addEventListener('toggle',()=>localStorage.setItem('resource-open',String(fold.open)));
  const tip=el('div',null,'resource-tip');tip.hidden=true;document.body.append(tip);
  function showTip(event,row){
    const input=plan.input_jobs?.find(x=>x.id===row.id)||{};
    const lines=[row.title,t('时间：','Time: ')+(row.finish?date(row.start)+' → '+date(row.finish):t('结束时间还排不出','Finish awaits a measured plan')),t('做什么：','Purpose: ')+(input.purpose||row.title)];
    if(['paused','waiting_review','waiting_human'].includes(row.state))lines.push(t('原因：','Reason: ')+(input.reason||t('等待负责人安排','Waiting for the project lead')));
    tip.textContent=lines.join('\n');tip.hidden=false;
    const box=event.currentTarget.getBoundingClientRect();tip.style.left=Math.max(8,Math.min(innerWidth-tip.offsetWidth-8,box.left))+'px';tip.style.top=Math.max(8,Math.min(innerHeight-tip.offsetHeight-8,box.bottom+8))+'px';
  }
  function draw(){
    if(!plan)return;const pos=viewport.scrollLeft;grid.replaceChildren();
    const now=new Date(plan.now).getTime(),starts=plan.jobs.filter(r=>r.start).map(r=>new Date(r.start).getTime()),ends=plan.jobs.filter(r=>r.finish).map(r=>new Date(r.finish).getTime());
    origin=Math.min(now-6*3600000,...starts);
    const hours=Math.max(18,(Math.max(now,...ends)-origin)/3600000+2),width=nameWidth()+hours*pph;
    grid.style.width=width+'px';const axis=el('div',null,'resource-row');axis.append(el('span',t('实验','Experiment'),'resource-label'));
    const every=pph<30?6:pph<60?3:1;for(let h=0;h<=hours;h+=every){const tick=el('span',date(origin+h*3600000),'resource-hour');tick.style.left=(nameWidth()+h*pph)+'px';axis.append(tick);}grid.append(axis);
    const nowLine=el('div',null,'resource-now');nowLine.style.left=(nameWidth()+(now-origin)/3600000*pph)+'px';nowLine.setAttribute('aria-label',t('现在','Now'));grid.append(nowLine);
    for(const row of plan.jobs.filter(r=>r.state!=='done')){
      const line=el('div',null,'resource-row'),label=el('span',row.title,'resource-label');line.append(label);
      if(row.start&&row.finish){const bar=el('button',null,'resource-bar '+row.state);bar.type='button';bar.style.left=(nameWidth()+(new Date(row.start)-origin)/3600000*pph)+'px';bar.style.width=Math.max(3,(new Date(row.finish)-new Date(row.start))/3600000*pph)+'px';bar.setAttribute('aria-label',row.title+' '+date(row.finish));bar.addEventListener('pointerenter',e=>showTip(e,row));bar.addEventListener('focus',e=>showTip(e,row));bar.addEventListener('pointerleave',()=>tip.hidden=true);bar.addEventListener('blur',()=>tip.hidden=true);bar.addEventListener('click',()=>{tip.hidden=true;const entries=typeof treeNodes==='function'?treeNodes():[];const entry=entries.find(x=>row.task&&(x.node.tasks||[]).includes(row.task))||entries.find(x=>x.node.title===row.title);const card=entry&&[...document.querySelectorAll('#tree-body .nd')].find(n=>n.dataset.key===entry.key);if(card)card.click();});line.append(bar);}
      else line.append(el('span',row.state==='waiting_trial'?t('待试跑','Trial needed'):row.state==='paused'?t('暂停','Paused'):t('等前置','Waiting for prerequisite'),'resource-wait'));
      grid.append(line);
    }
    viewport.scrollLeft=pos;
    if(!manual)center();
  }
  viewport.addEventListener('wheel',e=>{if(e.ctrlKey){e.preventDefault();zoom(pph*Math.exp(-e.deltaY*.004),e.clientX-viewport.getBoundingClientRect().left);}},{passive:false});
  let drag=null;
  viewport.addEventListener('pointerdown',e=>{
    if(e.pointerType==='touch')return;
    if(e.button===0&&!e.target.closest('button')){drag={x:e.clientX,left:viewport.scrollLeft};viewport.setPointerCapture(e.pointerId);viewport.classList.add('dragging');}
  });
  viewport.addEventListener('pointermove',e=>{if(drag){viewport.scrollLeft=drag.left+drag.x-e.clientX;manual=true;}});
  const end=()=>{drag=null;viewport.classList.remove('dragging');};
  viewport.addEventListener('pointerup',end);viewport.addEventListener('pointercancel',end);
  let gesture=null;
  viewport.addEventListener('touchstart',e=>{if(e.touches.length===2){const a=e.touches[0],b=e.touches[1];gesture={distance:Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY),pph};}},{passive:true});
  viewport.addEventListener('touchmove',e=>{if(gesture&&e.touches.length===2){e.preventDefault();const a=e.touches[0],b=e.touches[1];zoom(gesture.pph*Math.hypot(a.clientX-b.clientX,a.clientY-b.clientY)/Math.max(1,gesture.distance),(a.clientX+b.clientX)/2-viewport.getBoundingClientRect().left);}},{passive:false});
  viewport.addEventListener('touchend',()=>gesture=null);
  viewport.addEventListener('scroll',()=>{if(plan){localStorage.setItem('resource-scroll',String(viewport.scrollLeft));}});
  const dialog=el('dialog',null,'packet-dialog'),head=el('header'),heading=el('h2',t('外置大脑','Manual research packets')),close=el('button',t('关闭','Close')),body=el('div');
  close.type='button';close.addEventListener('click',()=>dialog.close());head.append(heading,close);dialog.append(head,body);document.body.append(dialog);
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
  const nav=document.getElementById('nav'),open=el('button',t('外置大脑','Manual research packets'),'packet-open');open.type='button';open.hidden=true;
  open.addEventListener('click',()=>dialog.showModal());nav.append(open);
  const file=(packet,name)=>'/manual-packets/'+encodeURIComponent(packet.name)+'/'+encodeURIComponent(name);
  function packets(rows){
    open.hidden=!rows.length;body.replaceChildren();
    for(const p of rows){const article=el('article');article.append(el('h3',p.title),el('pre',p.question));const copy=el('button',t('复制提问','Copy question'));copy.type='button';copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(p.question);copy.textContent=t('已复制','Copied');}catch{copy.textContent=t('选中文字复制','Select the question to copy');}});article.append(copy);
      for(const name of p.attachments||[]){const a=el('a',name);a.href=file(p,name);a.target='_blank';a.rel='noopener';article.append(a);}
      const list=el('ul');for(const [i,v] of (p.answer_versions||[]).entries()){const li=el('li'),a=el('a',t('回答 ','Answer ')+(i+1));a.href=file(p,v.answer);a.target='_blank';a.rel='noopener';li.append(a);const review=v.review;if(review){const labels={accepted:t('采用','Accepted'),partial:t('部分采用','Partly accepted'),rejected:t('退回','Returned')};li.append(el('strong',labels[review.decision]||review.decision),el('p',review.note+(review.task?' → '+review.task:'')));}if(p.adopted_answer===v.id)li.append(el('span',t(' · 当前采用版本',' · Adopted version')));for(const name of v.files||[]){const f=el('a',name);f.href=file(p,name);f.target='_blank';f.rel='noopener';li.append(f);}list.append(li);}article.append(list);body.append(article);
    }
  }
  window.addEventListener('overview',e=>{
    const o=e.detail.overview||{};issues.hidden=!(o.research_issues||[]).length;issues.textContent=(o.research_issues||[]).map(x=>x.section==='resource_plan'?t('请检查资源计划的作业与测量单位','Check the resource plan jobs and measured units'):t('请检查研究包 ','Check manual packet ')+(x.name||'')).join(' · ');packets(o.manual_packets||[]);const next=o.resource_plan;fold.hidden=!next;if(!next)return;plan=next;
    summary.textContent=t('剩余约 ','Remaining ')+Number(plan.remaining_card_hours).toFixed(1)+t(' 卡时',' card-hours')+(plan.finish?t(' · 排完约 ',' · Finish ')+date(plan.finish):'');
    summary.title=t('采样：','Observed: ')+date(plan.observed_at*1000)+t('；计算：','; calculated: ')+date(plan.now);
    const key=JSON.stringify(plan);if(key!==signature){signature=key;const saved=localStorage.getItem('resource-scroll');draw();if(manual&&saved!==null)viewport.scrollLeft=Number(saved)||0;}
  });
  new ResizeObserver(()=>draw()).observe(viewport);
})();

(() => {
  const host=document.getElementById('tasks');if(!host)return;
  const fold=document.createElement('details'),heading=document.createElement('summary'),list=document.createElement('div');
  fold.id='delivery-stages';heading.textContent='阶段交付 / Stage deliveries';fold.append(heading,list);host.append(fold);fold.hidden=true;
  window.addEventListener('overview',event=>{
    const rows=((event.detail||{}).overview||{}).delivery_stages||[];fold.hidden=!rows.length;list.replaceChildren();
    for(const row of rows){const line=document.createElement('p');line.textContent=row.task+' · '+row.stage+' · '+row.state;list.append(line);}
  });
})();
