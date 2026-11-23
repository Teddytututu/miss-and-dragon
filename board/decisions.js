/* Owner choices reuse the existing board refresh and appearance. */
(() => {
  const host=document.getElementById('todo');if(!host)return;
  const area=document.createElement('div');area.id='decision-cards';host.prepend(area);
  const t=(zh,en)=>document.documentElement.lang.startsWith('zh')?zh:en;
  window.addEventListener('overview',event=>{
    const overview=event.detail.overview||{},creators=overview.decision_policy?.creators||['Claude'];area.replaceChildren();
    for(const row of overview.decisions||[]){
      if(row.acked_at||!creators.includes(row.by))continue;
      const card=document.createElement('article');card.className='card';
      const title=document.createElement('h3'),why=document.createElement('p'),status=document.createElement('p');title.textContent=row.title;why.textContent=row.why;status.setAttribute('role','status');card.append(title,why);
      const note=document.createElement('input');note.maxLength=80;note.value=row.note||'';note.placeholder=t('补充说明','Additional note');note.setAttribute('aria-label',note.placeholder);
      const options=document.createElement('div');card.append(options,note,status);
      row.options.forEach((label,index)=>{
        const button=document.createElement('button');button.type='button';button.textContent=label+(row.recommend===index?t(' · 推荐',' · Recommended'):'');button.setAttribute('aria-pressed',String(row.chosen===index));
        button.onclick=async()=>{
          options.querySelectorAll('button').forEach(b=>b.disabled=true);
          try{const r=await fetch('/api/decision',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:row.id,option:index,note:note.value})});if(!r.ok)throw Error(t('请重试','Please try again'));row.chosen=index;options.querySelectorAll('button').forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));status.textContent=t('选择已保存','Choice saved');}catch(e){status.textContent=e.message;}finally{options.querySelectorAll('button').forEach(b=>b.disabled=false);}
        };options.append(button);
      });area.append(card);
    }
  });
})();
