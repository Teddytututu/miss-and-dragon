/* Full-screen cadence and the user's identity menu. */
(()=>{
 const $=s=>document.querySelector(s),make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;};
 const en=()=>window.BoardI18n?.language==='en';
 const t=(zh,english)=>en()?english:zh;
 const api=async(url,body)=>{const r=await fetch(url,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const v=await r.json();if(!r.ok)throw Error(v.error||t('请稍后重试','Try again'));return v;};
 const remembered=(key,value)=>{try{if(value===undefined)return localStorage.getItem(key);localStorage.setItem(key,value);}catch(_){}return null;};
 let data,project,trigger;
 const dialog=make('dialog',null,'cadence-panel');dialog.id='cadence-panel';dialog.setAttribute('aria-labelledby','cadence-title');
 const heading=make('header',null,'cadence-header'),title=make('h2');title.id='cadence-title';const close=make('button');close.type='button';heading.append(title,close);
 const status=make('p',null,'cadence-status');status.setAttribute('role','status');
 const body=make('div',null,'cadence-body');dialog.append(heading,status,body);document.body.append(dialog);
 const error=e=>{status.textContent=e.message;};
 function hide(){dialog.close();remembered('board-cadence-open','0');trigger?.focus();}
 close.onclick=hide;dialog.addEventListener('cancel',e=>{e.preventDefault();hide();});
 async function save(payload){const old=document.activeElement,row=old?.closest('tr'),key=row?.dataset.item,index=row?Array.from(row.querySelectorAll('button,input,select')).indexOf(old):-1;data=await api('/api/cadence',payload);render();if(key&&index>=0)body.querySelector('tr[data-item="'+key+'"]')?.querySelectorAll('button,input,select')[index]?.focus({preventScroll:true});status.textContent=t('已保存','Saved');}
 function button(zh,english,action){const b=make('button',t(zh,english));b.type='button';b.onclick=()=>Promise.resolve(action()).catch(error);return b;}
 function label(text,input){const l=make('label',text);l.append(input);return l;}
 function input(type,value){const n=make('input');n.type=type;n.value=value;return n;}
 function render(){
  title.textContent=t('节奏设置','Cadence settings');close.textContent=t('收起','Close');body.replaceChildren();
  body.append(make('p',t('程序负责频繁检查，助手按额度巡检。固定间隔仍遵循提及、临近截止与额度暂停规则。','Programs check frequently; assistants patrol according to quota. Fixed intervals retain mention, deadline and low-quota safeguards.')));
  const table=make('table');table.className='cadence-table';const head=make('thead'),tr=make('tr');
  for(const [zh,english] of [['优先级','Priority'],['事项','Activity'],['谁执行','Who'],['默认','Default'],['当前','Current'],['下次','Next']])tr.append(make('th',t(zh,english)));head.append(tr);table.append(head);
  const rows=make('tbody');
  data.items.forEach((item,i)=>{
   const row=make('tr');row.dataset.item=item.id;if(item.override)row.className='cadence-overridden';
   const cells=Array.from({length:6},()=>make('td'));row.append(...cells);
   const order=make('div',null,'cadence-order');order.append(make('strong',String(i+1)));
   for(const [offset,zh,english]of [[-1,'上移','Move up'],[1,'下移','Move down']]){const b=button(offset<0?'↑':'↓',offset<0?'↑':'↓',()=>{const ids=data.order.slice();[ids[i],ids[i+offset]]=[ids[i+offset],ids[i]];return save({order:ids});});b.disabled=i+offset<0||i+offset>=data.items.length;b.setAttribute('aria-label',t(zh,english)+' '+(en()?item.name_en:item.name));order.append(b);}cells[0].append(order);
   cells[1].append(make('strong',en()?item.name_en:item.name),make('small',en()?item.description_en:item.description));
   const actors={'program':t('程序','Program'),'program → Dragon':t('程序 → 龙娘','Program → Dragon'),'GPT':t('龙娘','Dragon'),'Claude':t('大小姐','Miss'),'Claude → GPT':t('大小姐定 · 龙娘做','Miss plans · Dragon does')};cells[2].textContent=actors[item.actor]||item.actor;
   const model=item.kind==='model',numeric=model||item.kind==='program';
   let base=numeric?`${item.suggested_minutes} ${t('分钟','min')}`:item.kind==='daily'?t('每天 19:00','Daily 19:00'):item.id==='weekly_rules'?t('周日，整理后','Sunday, after tidy'):t('周日 20:00','Sunday 20:00');
   if(item.id==='event_cooldown')base=t('立即 · 冷却 5 分钟','Immediate · 5 min cooldown');
   cells[3].append(make('strong',base),make('small',en()?item.reason_en:item.reason));
   const form=make('form',null,'cadence-controls');let setting;
   if(numeric){const n=input('number',item.override?.minutes??item.suggested_minutes);n.min=model?20:1;n.max=model?1440:60;n.step=1;n.required=true;n.setAttribute('aria-label',(en()?item.name_en:item.name)+' '+t('分钟','minutes'));
    if(model){const mode=make('select');for(const [v,zh,english]of [['auto','自动 · 按额度','Automatic · quota'],['fixed','固定间隔','Fixed interval']]){const o=make('option',t(zh,english));o.value=v;mode.append(o);}mode.setAttribute('aria-label',(en()?item.name_en:item.name)+' '+t('巡检模式','patrol mode'));mode.value=item.override?'fixed':'auto';n.disabled=mode.value==='auto';mode.onchange=()=>{n.disabled=mode.value==='auto';};form.append(mode);setting=()=>mode.value==='auto'?null:{minutes:Number(n.value)};}
    else setting=()=>({minutes:Number(n.value)});
    form.append(n);
   }else{const clock=input('time',item.time);clock.required=true;let day;
    if(item.kind==='weekly'){day=make('select');const names=en()?['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']:['周一','周二','周三','周四','周五','周六','周日'];names.forEach((n,i)=>{const o=make('option',n);o.value=i;day.append(o);});day.value=item.weekday;day.setAttribute('aria-label',t('星期','Weekday'));form.append(day);}
    clock.setAttribute('aria-label',t('时间','Time'));form.append(clock);
    let after;if(item.id==='weekly_rules'){after=input('checkbox','');after.checked=!!item.after;form.append(label(t('接在整理后','After tidy'),after));clock.disabled=after.checked;day.disabled=after.checked;after.onchange=()=>{clock.disabled=after.checked;day.disabled=after.checked;};}
    setting=()=>({...day?{weekday:Number(day.value)}:{},time:clock.value,...after?{after:after.checked?'weekly_tidy':null}:{}});
   }
   const submit=make('button',t('保存','Save'));submit.type='submit';form.append(submit);
   form.onsubmit=async e=>{e.preventDefault();try{await save({overrides:{[item.id]:setting()}});}catch(e){error(e);}};
   form.append(button('恢复默认','Reset',()=>save({overrides:{[item.id]:null}})));cells[4].append(form);
   cells[5].textContent=item.next_wake?new Date(item.next_wake*1000).toLocaleString(en()?'en':'zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):item.id==='weekly_rules'?t('整理完成并确认后','After tidy acknowledgement'):item.kind==='model'?t('按额度计算','Calculated from quota'):t('程序按设置运行','Program managed');
   rows.append(row);
  });table.append(rows);body.append(table,button('恢复默认顺序','Reset order',()=>save({order:data.default_order})));
  const section=make('section',null,'cadence-project'),form=make('form');section.append(make('h3',t('项目信息','Project information')));
  const q=make('textarea');q.value=project.question||'';q.required=true;q.maxLength=2000;const d=make('textarea');d.value=project.deliverable||'';d.required=true;d.maxLength=2000;
  form.append(label(t('研究问题','Research question'),q),label(t('想要的成果','Desired deliverable'),d));const b=make('button',t('保存项目信息','Save project information'));b.type='submit';form.append(b);form.onsubmit=async e=>{e.preventDefault();try{project=await api('/api/project',{question:q.value,deliverable:d.value});status.textContent=t('已保存','Saved');}catch(e){error(e);}};section.append(form);body.append(section);
 }
 async function open(){trigger=$('#cadence-open');status.textContent=t('正在读取','Loading');dialog.showModal();remembered('board-cadence-open','1');try{[data,project]=await Promise.all([api('/api/cadence'),api('/api/project')]);render();status.textContent='';close.focus();}catch(e){error(e);}}
 async function init(){await BoardIdentity.ready;
  const bar=make('div',null,'cadence-launch');const launch=button('节奏设置','Cadence settings',open);launch.id='cadence-open';launch.setAttribute('aria-haspopup','dialog');
  const identity=make('details',null,'cadence-identity'),summary=make('summary',BoardIdentity.name('owner')+' ▾');identity.append(summary);
  const form=make('form'),name=input('text',BoardIdentity.name('owner'));name.maxLength=40;name.required=true;form.append(label(t('你的显示名','Your display name'),name));const save=make('button',t('保存显示名','Save display name'));save.type='submit';form.append(save);const s=make('p');s.setAttribute('role','status');form.append(s);form.onsubmit=async e=>{e.preventDefault();try{await api('/api/display-name',{user_name:name.value});await BoardIdentity.refreshAccounts();summary.textContent=BoardIdentity.name('owner')+' ▾';s.textContent=t('已保存','Saved');}catch(e){s.textContent=e.message;}};identity.append(form);bar.append(launch,identity);$('#agent-panel').after(bar);
  window.addEventListener('languagechange',()=>{launch.textContent=t('节奏设置','Cadence settings');if(data)render();});
  if(remembered('board-cadence-open')==='1')await open();
 }
 init().catch(error);
})();
