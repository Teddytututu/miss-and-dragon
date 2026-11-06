/* Existing paper wall, with owner-authored notes and reversible completion. */
(() => {
  'use strict';
  const nodes=new Map(), busy=new Set();
  let config={},lastKey='',archive,announcementTimer;
  const make=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!=null)n.textContent=text;return n;};
  const uuid=()=>crypto.randomUUID();
  const timeLabel=value=>new Date(value).toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'});
  async function send(payload) {
    const response=await fetch('/api/todo/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const data=await response.json();if(!response.ok)throw Error(data.error||'请重试保存。');return data;
  }
  function announce(text) {
    let n=document.getElementById('note-announcement');
    if(!n){n=make('div','note-announcement');n.id='note-announcement';n.setAttribute('role','status');document.body.append(n);}
    clearTimeout(announcementTimer);
    n.textContent=text;
    announcementTimer=setTimeout(()=>n.remove(),4000);
  }
  async function schedule(node,row) {
    if(busy.has(row.note_id))return;
    busy.add(row.note_id);node.setAttribute('aria-busy','true');
    try {
      const result=await send({op:'schedule',id:row.note_id,client_id:uuid()});
      render(result.todo,result.todo_done,config);config.refresh?.();announce('已放进今天，等助手排时间。');
    }catch(error){announce(error.message);}
    finally{busy.delete(row.note_id);node.removeAttribute('aria-busy');}
  }
  function menu(node,row) {
    let action;
    const dialog=make('dialog','note-menu');dialog.setAttribute('aria-label','便利贴操作');
    const reply=make('button','','回一句'),today=make('button','','放进今天'),cancel=make('button','','取消');
    for(const button of [reply,today,cancel])button.type='button';
    dialog.append(reply,today,cancel);document.body.append(dialog);
    const close=()=>dialog.close();
    reply.onclick=()=>{action=()=>write(node,row);close();};today.onclick=()=>{action=()=>schedule(node,row);close();};cancel.onclick=close;
    dialog.addEventListener('close',()=>{dialog.remove();if(action)action();else if(node.isConnected)node.focus({preventScroll:true});});
    dialog.onclick=event=>{if(event.target===dialog){const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)close();}};
    dialog.showModal();
  }
  function attachToday(card) {
    card.classList.add('note-today-drop');
    const accepts=event=>Array.from(event.dataTransfer?.types||[]).includes('application/x-board-note');
    card.addEventListener('dragover',event=>{if(accepts(event)){event.preventDefault();event.dataTransfer.dropEffect='move';card.classList.add('note-drop-active');}});
    card.addEventListener('dragleave',event=>{if(!card.contains(event.relatedTarget))card.classList.remove('note-drop-active');});
    card.addEventListener('drop',event=>{
      card.classList.remove('note-drop-active');if(!accepts(event))return;event.preventDefault();
      const id=event.dataTransfer.getData('application/x-board-note'),node=nodes.get(id),row=node?._noteRow;
      if(row)schedule(node,row);
    });
  }
  document.addEventListener('dragend',()=>document.querySelectorAll('.note-drop-active').forEach(card=>card.classList.remove('note-drop-active')));
  function comments(node,row) {
    let host=node.querySelector('.note-replies');
    if(!host){host=make('div','note-replies');node.insertBefore(host,node.querySelector('.note-actions'));}
    const key=JSON.stringify(row.note_replies||[]);if(host.dataset.key===key)return;
    host.dataset.key=key;host.replaceChildren();
    for(const reply of row.note_replies||[]){
      const line=make('div','note-reply');line.append(make('span','',reply.text),make('time','',timeLabel(reply.at)));host.append(line);
    }
  }
  function write(node,row) {
    if(node.querySelector('.note-write')){node.querySelector('input').focus();return;}
    const form=make('form','note-write'),input=make('input'),status=make('span','note-write-status');
    const bar=make('div','note-write-bar'),count=make('span','note-write-count','0/40'),cancel=make('button','note-write-cancel','取消'),ok=make('button','note-write-send','发送');
    cancel.type='button';ok.type='submit';
    input.type='text';input.maxLength=40;input.placeholder='写一句…';input.autocomplete='off';
    input.setAttribute('aria-label','回复便利贴：'+row.what);status.setAttribute('role','status');
    bar.append(count,cancel,ok);form.append(input,bar,status);node.append(form);input.focus();
    const close=()=>{form.remove();node.querySelector('.note-reply-trigger')?.focus();};
    input.oninput=()=>{const n=Array.from(input.value).length;count.textContent=n+'/40';count.classList.toggle('full',n>=40);};
    cancel.onclick=close;
    form.addEventListener('focusout',()=>setTimeout(()=>{if(form.isConnected&&!form.contains(document.activeElement)&&!input.value.trim())close();},120));
    input.onkeydown=e=>{if(e.isComposing&&e.key==='Enter'){e.preventDefault();return;}if(e.key==='Escape')close();};
    form.onsubmit=async e=>{
      e.preventDefault();e.stopPropagation();const text=input.value.trim();
      if(!text||input.disabled)return;
      if(Array.from(text).length>40){status.textContent='最多40字';return;}
      input.disabled=true;status.textContent='';
      try {const result=await send({op:'reply',id:row.note_id,text,client_id:uuid()});form.remove();render(result.todo,result.todo_done,config);config.refresh?.();}
      catch(error){status.textContent=error.message;input.disabled=false;input.focus();}
    };
  }
  function gestures(node,row) {
    let start=null,timer;
    node.addEventListener('keydown',event=>{
      if(event.target===node&&['Enter',' '].includes(event.key)){event.preventDefault();write(node,node._noteRow);}
    });
    const cancel=()=>{clearTimeout(timer);start=null;};
    node.addEventListener('pointerdown',event=>{
      if(event.pointerType!=='touch'||event.target.closest('a,button,input,form'))return;
      start={x:event.clientX,y:event.clientY};
      timer=setTimeout(()=>{start=null;menu(node,node._noteRow);},550);
    });
    node.addEventListener('pointermove',event=>{if(start&&Math.hypot(event.clientX-start.x,event.clientY-start.y)>10)cancel();});
    node.addEventListener('pointerup',cancel);node.addEventListener('pointercancel',cancel);
  }
  function card(row) {
    let node=nodes.get(row.note_id);
    if(!node){
      const wc=config.whenClass(row.when||'');node=make('div','todo-item '+wc);node.dataset.noteId=row.note_id;
      const top=make('div','todo-top');top.append(make('span','todo-what',row.what),make('span','todo-when '+wc,row.when||''));node.append(top);
      if(row.why)node.append(make('div','muted small',row.why));
      if(row.how){const h=make('div','small todo-how');h.append(config.linkOrText(row.how));node.append(h);}
      node.dataset.wallText=node.textContent;node.tabIndex=0;node.setAttribute('aria-label',row.what+'，回车写一句');
      const actions=make('div','note-actions'),reply=make('button','note-reply-trigger','✎ 回一句');reply.type='button';reply.setAttribute('aria-label','回复便利贴：'+row.what);reply.onclick=()=>write(node,row);actions.append(reply);node.append(actions);
      const drag=make('button','note-schedule-drag','⋮⋮');drag.type='button';drag.draggable=true;drag.title='拖进今天';drag.setAttribute('aria-label','拖进今天：'+row.what);
      drag.ondragstart=event=>{event.dataTransfer.setData('application/x-board-note',row.note_id);event.dataTransfer.effectAllowed='move';event.dataTransfer.setDragImage(node,16,16);};
      drag.onclick=()=>schedule(node,row);actions.prepend(drag);
      gestures(node,row);nodes.set(row.note_id,node);
    }
    node._noteRow=row;
    let returned=node.querySelector('.note-returned');
    if(row.returned_yesterday&&!returned){returned=make('span','note-returned','昨天没做');node.querySelector('.todo-top').after(returned);}
    if(!row.returned_yesterday)returned?.remove();
    comments(node,row);return node;
  }
  function completed(rows) {
    if(!archive){archive=make('details','todo-archive');archive.id='todo-archive';document.getElementById('todo-list').after(archive);}
    archive.hidden=!rows.length;const opened=archive.open;
    const summary=make('summary','','已处理 · '+rows.length),body=make('div','todo-archive-body');
    const fill=()=>{if(body.childElementCount)return;for(const row of rows.slice().reverse()){
      const line=make('div','todo-archive-line');line.append(make('span','',row.what),make('time','',row.done_at?timeLabel(row.done_at):''));body.append(line);
    }};
    archive.replaceChildren(summary,body);archive.open=opened;if(opened)fill();archive.ontoggle=()=>{if(archive.open)fill();};
  }
  function render(todo,done,options) {
    config=options||config;const box=document.getElementById('todo-list');
    const key=JSON.stringify([todo,done]);if(key===lastKey)return;lastKey=key;
    document.getElementById('todo-n').textContent=todo.length||'';
    const focus=document.activeElement,live=new Set(todo.map(row=>row.note_id));
    for(const id of nodes.keys())if(!live.has(id))nodes.delete(id);
    const desired=todo.map(card),keep=new Set(desired);
    for(const child of [...box.children])if(!keep.has(child))child.remove();
    desired.forEach((node,i)=>{if(box.children[i]!==node)box.insertBefore(node,box.children[i]||null);});
    if(!todo.length)box.append(make('div','muted','现在没有要你做的事。'));
    if(focus?.isConnected)focus.focus({preventScroll:true});completed(done||[]);
  }
  window.TodoNotes={render,attachToday};
})();
