
window.DiscussionRoom = (() => {
  let key = '';
  let items = [], limit = 18, sending = false, lastRevision = '', draft, expanded = new Set(), pending = [], inputHeightPreference=null;
  const $ = selector => document.querySelector(selector);
  const sizing = {
    clampScale(value) { const n=value==null?NaN:Number(value);return Number.isFinite(n)?Math.round(Math.max(.8,Math.min(1.6,n))*10)/10:1; },
    zoomKey(event) {
      if(!(event.ctrlKey||event.metaKey)||event.altKey||event.isComposing)return null;
      return ['=','+'].includes(event.key)?1:['-','_'].includes(event.key)?-1:event.key==='0'?0:null;
    },
    nearestStop(height,available) { return [.45,.75,1].reduce((best,n)=>Math.abs(height-available*n)<Math.abs(height-available*best)?n:best,.45); },
    dismissDrawer(stop,delta) { return stop===.45&&delta>80; },
    clampInputHeight(value,min,max) { const n=Number(value);return Math.round(Math.max(min,Math.min(max,Number.isFinite(n)?n:min))); },
    visibleFrame(viewport,fallbackHeight,layoutHeight=0,baselineHeight=0) {
      const height=Number(viewport?.height),top=Number(viewport?.offsetTop);
      const frame={height:Number.isFinite(height)&&height>0?height:fallbackHeight,top:Number.isFinite(top)?Math.max(0,top):0};
      // resizes-content browsers can shrink layout and visual viewports separately.
      // Use the resized content bottom rather than subtracting browser chrome twice.
      const contentResized=baselineHeight-layoutHeight>120&&Math.abs(layoutHeight-fallbackHeight)<2&&Math.abs((viewport?.scale??1)-1)<.01;
      if(contentResized)frame.height=Math.max(frame.height,layoutHeight-frame.top);
      return frame;
    }
  };
  function initSizing() {
    const box=$('#msgs'),header=box.querySelector('.room-header'),root=document.documentElement;
    $('#room-threads').tabIndex=0;
    const read=(key,fallback)=>{try{return localStorage.getItem(key)??fallback;}catch(_){return fallback;}};
    const write=(key,value)=>{try{localStorage.setItem(key,String(value));}catch(_){}};
    let scale=sizing.clampScale(read('roomScale','1')),hovered=false,hintTimer;
    const hint=node('span','room-scale-hint');hint.setAttribute('role','status');hint.setAttribute('aria-live','polite');box.append(hint);
    const scope=target=>!!target?.closest?.('#msgs,.avatar-mood-picker[open],.room-message-menu,.room-reaction-actors');
    const changeScale=(value,announce=true)=>{
      const logs=[...box.querySelectorAll('.room-threads,.private-log')];
      const anchors=logs.map(log=>({log,bottom:log.scrollHeight-log.scrollTop-log.clientHeight<36,top:log.scrollTop}));
      scale=sizing.clampScale(value);root.style.setProperty('--room-scale',scale);write('roomScale',scale);
      if(announce){hint.textContent=(window.BoardI18n?.language==='en'?'Discussion ':'讨论室 ')+Math.round(scale*100)+'%';hint.classList.add('show');clearTimeout(hintTimer);hintTimer=setTimeout(()=>hint.classList.remove('show'),1000);}
      requestAnimationFrame(()=>{resizeInput();for(const a of anchors)a.log.scrollTop=a.bottom?a.log.scrollHeight:a.top;});
    };
    changeScale(scale,false);
    document.addEventListener('pointerover',event=>{hovered=scope(event.target);},{passive:true});
    document.addEventListener('pointerout',event=>{hovered=scope(event.relatedTarget);},{passive:true});
    document.addEventListener('keydown',event=>{
      const step=sizing.zoomKey(event);
      if(step===null||(!scope(document.activeElement)&&!hovered))return;
      event.preventDefault();changeScale(step===0?1:scale+step*.1);
    },true);
    document.addEventListener('wheel',event=>{
      if(!event.ctrlKey||(!scope(event.target)&&!scope(document.activeElement)))return;
      event.preventDefault();if(event.deltaY)changeScale(scale+(event.deltaY<0?.1:-.1));
    },{passive:false,capture:true});
    const mobile=matchMedia('(max-width:719px)'),phone=matchMedia('(max-width:600px)');
    inputHeightPreference=Number(read('roomInputHeight','0'))||null;
    let stop=Number(read('roomDrawerStop','.75'));if(![.45,.75,1].includes(stop))stop=.75;
    let available=0,drag=null,keyboard=false,baseline=innerHeight;
    function fitDrawer() {
      const full=phone.matches&&box.classList.contains('dock')&&!box.classList.contains('collapsed');
      document.body.classList.toggle('room-mobile-open',full);
      root.classList.toggle('room-mobile-open',full);
      header.setAttribute('aria-label',phone.matches?'讨论室':'讨论室标题，手机可拖动调整高度');
      if(!mobile.matches){if(box.classList.contains('room-drawer-dragging'))box.classList.remove('room-drawer-dragging');return;}
      const focused=scope(document.activeElement)&&document.activeElement.matches('textarea,input,[contenteditable="true"]');
      if(!focused)baseline=innerHeight;else baseline=Math.max(baseline,innerHeight);
      const frame=sizing.visibleFrame(window.visualViewport,innerHeight,root.clientHeight,baseline),vh=frame.height,offset=frame.top;
      keyboard=!!focused&&baseline-vh>120;
      if(phone.matches){
        // Anchor directly to the visible top: mobile browsers resize innerHeight differently.
        box.style.setProperty('--room-drawer-top',offset+'px');
        box.style.setProperty('--room-drawer-height',Math.round(vh)+'px');
        box.dataset.keyboard=String(keyboard);resizeInput();return;
      }
      const nav=$('#nav'),r=nav?.getBoundingClientRect();
      const navHeight=r&&r.top>innerHeight/2?r.height:64;
      available=Math.max(160,vh-navHeight);
      box.style.setProperty('--room-drawer-bottom',Math.max(0,innerHeight-vh-offset)+navHeight+'px');
      box.style.setProperty('--room-drawer-height',Math.round(available*(keyboard?1:stop))+'px');
      box.dataset.drawerStop=String(stop);box.dataset.keyboard=String(keyboard);
    }
    const settle=value=>{stop=value;write('roomDrawerStop',stop);fitDrawer();};
    header.tabIndex=0;header.setAttribute('aria-label','讨论室标题，手机可拖动调整高度');
    header.addEventListener('keydown',event=>{
      if(phone.matches||!mobile.matches||event.target!==header||!['ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
      event.preventDefault();const stops=[.45,.75,1],i=stops.indexOf(stop);
      settle(event.key==='Home'?.45:event.key==='End'?1:stops[Math.max(0,Math.min(2,i+(event.key==='ArrowUp'?1:-1)))]);
    });
    header.addEventListener('pointerdown',event=>{
      if(phone.matches||!mobile.matches||keyboard||event.button!==0||event.target.closest('button,a,input,select,textarea,[role="button"]'))return;
      event.preventDefault();drag={id:event.pointerId,y:event.clientY,height:box.getBoundingClientRect().height,stop};
      header.setPointerCapture(event.pointerId);box.classList.add('room-drawer-dragging');
    });
    header.addEventListener('pointermove',event=>{
      if(!drag||drag.id!==event.pointerId)return;
      const height=Math.max(96,Math.min(available,drag.height+drag.y-event.clientY));
      box.style.setProperty('--room-drawer-height',height+'px');
    });
    const finish=(event,cancelled=false)=>{
      if(!drag||drag.id!==event.pointerId)return;
      const current=drag;drag=null;box.classList.remove('room-drawer-dragging');
      if(header.hasPointerCapture(event.pointerId))header.releasePointerCapture(event.pointerId);
      if(cancelled){settle(current.stop);return;}
      if(sizing.dismissDrawer(current.stop,event.clientY-current.y)){
        settle(.45);box.querySelector('.dock-close')?.click();
      }else settle(sizing.nearestStop(current.height+current.y-event.clientY,available));
    };
    header.addEventListener('pointerup',event=>finish(event));header.addEventListener('pointercancel',event=>finish(event,true));
    header.addEventListener('lostpointercapture',event=>{if(drag)finish(event,true);});
    const resizeHandle=node('button','room-input-resize','⤢');resizeHandle.type='button';
    resizeHandle.setAttribute('aria-label','调整输入框高度，上下方向键也可调整');
    resizeHandle.setAttribute('title','拖动调整输入框高度');$('#room-text').parentElement.append(resizeHandle);
    let inputDrag=null;
    const rememberInput=()=>write('roomInputHeight',inputHeightPreference||$('#room-text').getBoundingClientRect().height);
    resizeHandle.addEventListener('pointerdown',event=>{
      if(!phone.matches||event.button!==0)return;
      event.preventDefault();inputDrag={id:event.pointerId,y:event.clientY,height:$('#room-text').getBoundingClientRect().height};
      resizeHandle.setPointerCapture(event.pointerId);
    });
    resizeHandle.addEventListener('pointermove',event=>{
      if(!inputDrag||inputDrag.id!==event.pointerId)return;
      inputHeightPreference=inputDrag.height+inputDrag.y-event.clientY;resizeInput();
      inputHeightPreference=$('#room-text').getBoundingClientRect().height;
    });
    const finishInput=event=>{
      if(!inputDrag||inputDrag.id!==event.pointerId)return;inputDrag=null;rememberInput();
      if(resizeHandle.hasPointerCapture(event.pointerId))resizeHandle.releasePointerCapture(event.pointerId);
    };
    for(const name of ['pointerup','pointercancel','lostpointercapture'])resizeHandle.addEventListener(name,finishInput);
    resizeHandle.addEventListener('keydown',event=>{
      if(!phone.matches||!['ArrowUp','ArrowDown','Home','End'].includes(event.key))return;
      event.preventDefault();inputHeightPreference=event.key==='Home'?0:event.key==='End'?innerHeight:$('#room-text').getBoundingClientRect().height+(event.key==='ArrowUp'?24:-24);
      resizeInput();inputHeightPreference=$('#room-text').getBoundingClientRect().height;rememberInput();
    });
    box.addEventListener('focusin',fitDrawer);box.addEventListener('focusout',()=>requestAnimationFrame(fitDrawer));
    new MutationObserver(fitDrawer).observe(box,{attributes:true,attributeFilter:['class']});
    window.visualViewport?.addEventListener('resize',fitDrawer);window.visualViewport?.addEventListener('scroll',fitDrawer);
    window.addEventListener('resize',fitDrawer);mobile.addEventListener('change',fitDrawer);phone.addEventListener('change',()=>{resizeInput();fitDrawer();});fitDrawer();
  }
  const node = (tag, cls, text) => {
    const value = document.createElement(tag);
    if (cls) value.className = cls;
    if (text != null) value.textContent = text;
    return value;
  };
  const avatars = {};
  const channelPending=new Map(); let pendingChannel="main";
  let reader, reactionEmoji = ['👍','❤️','😂','🎉','👀','💡'];
  const markdownOptions = () => ({accounts:BoardIdentity.accounts, me:BoardIdentity.me.id});
  const avatarURL = (name, file) => BoardIdentity.avatarURL(name, file);
  let avatarDialog, avatarFullImage, avatarDialogTitle, avatarImageError, avatarClose, avatarTrigger, avatarFocus;
  function fitAvatar(image, asset) {
    if (/^\d+(?:\.\d+)?%$/.test(asset.cropWidth || '') && /^-?\d+(?:\.\d+)?%$/.test(asset.cropLeft || '') && /^-?\d+(?:\.\d+)?%$/.test(asset.cropTop || '')) {
      image.classList.add('avatar-crop-fill');Object.assign(image.style,{width:asset.cropWidth,left:asset.cropLeft,top:asset.cropTop});
    } else {
      image.classList.remove('avatar-crop-fill');for (const key of ['width','left','top']) image.style[key] = '';
      image.style.objectPosition = asset.position || '';
    }
  }
  function syncAvatars() {
    for (const account of BoardIdentity.accounts) {
      if (account.avatar) avatars[account.id] = {...account.avatar, label:account.display_name};
    }
    const members = document.querySelector('.room-members');
    if (members) { members.replaceChildren();
      for (const name of Object.keys(avatars)) {
        const button = node('button','room-avatar '+name.toLowerCase(),name[0]); button.type='button';
        decorateAvatar(button,name); members.append(button);
      }
    }
    const heading=document.querySelector('.room-heading span');
    if(heading) heading.textContent='发言者：'+BoardIdentity.name(BoardIdentity.me.id);
    const count=document.querySelector('.room-header-label');
    if(count) count.textContent=BoardIdentity.accounts.length+' 位成员';
  }
  function showAvatar(name, trigger) {
    const asset = avatars[name];
    if (!asset) return;
    if (!avatarDialog) {
      avatarDialog = node('dialog','room-avatar-dialog');
      avatarDialog.setAttribute('aria-labelledby','room-avatar-dialog-title');
      const header = node('div','room-avatar-dialog-header');
      avatarDialogTitle = node('h2'); avatarDialogTitle.id = 'room-avatar-dialog-title';
      avatarClose = node('button','room-avatar-close','关闭'); avatarClose.type = 'button'; avatarClose.autofocus = true;
      avatarClose.setAttribute('aria-label','关闭头像大图');
      avatarClose.onclick = () => avatarDialog.close();
      avatarFullImage = node('img','room-avatar-full');
      avatarImageError = node('p','room-avatar-error','头像图片加载遇到问题，请稍后重试。');
      avatarImageError.setAttribute('role','status'); avatarImageError.hidden = true;
      avatarFullImage.onerror = () => { avatarFullImage.hidden = true; avatarImageError.hidden = false; };
      header.append(avatarDialogTitle,avatarClose); avatarDialog.append(header,avatarFullImage,avatarImageError);
      avatarDialog.addEventListener('click',event => {
        if (event.target === avatarDialog || event.target === header) avatarDialog.close();
      });
      avatarDialog.addEventListener('keydown',event => { if (event.key === 'Escape') event.stopPropagation(); });
      avatarDialog.addEventListener('close',() => {
        let target = avatarTrigger;
        if (!target?.isConnected && avatarFocus?.messageId) {
          target = Array.from($('#room-threads').children).find(item => item.dataset.discussionId === avatarFocus.messageId)?.querySelector('.room-avatar');
        }
        if (!target?.isConnected && avatarFocus) target = document.querySelector('.room-members .room-avatar.'+avatarFocus.name.toLowerCase());
        target?.focus({preventScroll:true});
        avatarTrigger = null; avatarFocus = null;
      });
      document.body.append(avatarDialog);
    }
    avatarTrigger = trigger;
    avatarFocus = {name, messageId:trigger.closest('.room-message')?.dataset.discussionId};
    avatarDialogTitle.textContent = BoardIdentity.name(name)+'的头像';
    avatarFullImage.alt = BoardIdentity.name(name)+' · '+asset.label;
    avatarFullImage.hidden = false; avatarImageError.hidden = true;
    avatarFullImage.src = avatarURL(name,asset.full || asset.file);
    if (!avatarDialog.open) avatarDialog.showModal();
    avatarClose.focus({preventScroll:true});
  }
  function decorateAvatar(avatar, name) {
    avatar.dataset.mentionId = name;  // long press or right click inserts “@name ” (private-notes.js)
    const asset = avatars[name];
    if (!asset || avatar.querySelector('.room-avatar-image')) return;
    avatar.title = BoardIdentity.name(name)+' · '+asset.label;
    avatar.setAttribute('aria-label','查看'+BoardIdentity.name(name)+'的头像大图');
    avatar.setAttribute('aria-haspopup','dialog');
    avatar.onclick = () => showAvatar(name, avatar);
    const image = node('img','room-avatar-image');
    image.alt = ''; image.decoding = 'async';
    image.addEventListener('load',() => avatar.classList.add('room-avatar-ready'),{once:true});
    image.addEventListener('error',() => { image.remove(); avatar.classList.remove('room-avatar-ready'); },{once:true});
    image.src = avatarURL(name,asset.file);
    fitAvatar(image,asset);
    avatar.append(image);
  }
  function cleanText(body, protectCode = value => value) {
    let fence = null;
    const inline = text => {
      const code = [];
      text = text.replace(/(`+)(.+?)\1/g, (_, ticks, value) => '\u0000'+(code.push(value)-1)+'\u0000');
      text = text.replace(/!?\[([^\]]+)\]\(([^\s)]+)(?:\s+"[^"]*")?\)/g, (_, label, url) => label === url ? label : label+' '+url)
        .replace(/\*\*([^*\n]+)\*\*/g, '$1').replace(/__([^_\n]+)__/g, '$1')
        .replace(/~~([^~\n]+)~~/g, '$1').replace(/(^|\s)\*([^*\n]+)\*(?=\s|[，。；：！？,.!?]|$)/g, '$1$2')
        .replace(/(^|[\s（(：:，。])_([^_\n]+)_(?=[\s）)、，。；：！？,.!?]|$)/g, '$1$2');
      return text.replace(/\u0000(\d+)\u0000/g, (_, i) => protectCode(code[Number(i)]));
    };
    return String(body || '').replace(/<!--[\s\S]*?-->/g, '').replace(/\r\n?/g, '\n').split('\n').map(line => {
      const delimiter = line.match(/^\s{0,3}(`{3,}|~{3,})(.*)$/);
      if (delimiter && (!fence || (delimiter[1][0] === fence[0] && delimiter[1].length >= fence.length && !delimiter[2].trim()))) {
        fence = fence ? null : delimiter[1]; return '';
      }
      if (fence || /^(?: {4}|\t)/.test(line)) return protectCode(line);
      if (/^\s*(?:[-*_]\s*){3,}$/.test(line) || /^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line)) return '';
      line = line.replace(/^\s{0,3}#{1,6}\s+/, '').replace(/^\s*(?:>\s*)+/, '')
        .replace(/^\s*[-+*]\s+\[([ xX])\]\s*/, (_, value) => value === ' ' ? '○ ' : '✓ ')
        .replace(/^\s*[-+*]\s+/, '• ');
      if (/^\s*\|.*\|\s*$/.test(line)) line = line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim()).join('  ·  ');
      return inline(line);
    }).join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }
  const excerpt = body => cleanText(body).replace(/\s+/g, ' ').slice(0, 76);
  function restoreDraft() {
  const owner=BoardIdentity.me.identities?.includes('owner')?'owner':BoardIdentity.me.id;
  key = 'research-discussion-'+owner+'-'+BoardIdentity.channel;
  try { draft = JSON.parse(localStorage.getItem(key) || '{}'); } catch (_) { draft = {}; }
  if (!draft || typeof draft !== 'object' || Array.isArray(draft)) draft = {};
  if (typeof draft.body !== 'string') draft.body = '';
  if (typeof draft.parent_id !== 'string') draft.parent_id = null;
  }
  const save = () => { try { localStorage.setItem(key, JSON.stringify(draft)); } catch (_) {} };
  function status(message, error = false) {
    $('#room-status').textContent = message;
    $('#room-status').classList.toggle('error', error);
  }
  function composer() {
    const parent = items.find(item => item.id === draft.parent_id);
    $('#room-reply-context').hidden = !draft.parent_id;
    $('#room-reply-label').textContent = parent?.deleted ? '原消息已撤回' : parent ? '回复 '+BoardIdentity.name(parent.author)+'：'+excerpt(parent.body) : '回复所选消息';
    $('#room-submit').setAttribute('aria-label', draft.parent_id ? '发送回复' : '发送消息');
  }
  function resizeInput() {
    const input = $('#room-text');
    if(matchMedia('(max-width:600px)').matches){
      const style=getComputedStyle(input),line=parseFloat(style.lineHeight)||parseFloat(style.fontSize)*1.5;
      const min=Math.ceil(line+parseFloat(style.paddingTop)+parseFloat(style.paddingBottom)+2);
      const frameHeight=parseFloat($('#msgs').style.getPropertyValue('--room-drawer-height'))||window.visualViewport?.height||innerHeight;
      const max=Math.max(min,Math.floor(frameHeight/2));
      const height=sizing.clampInputHeight(inputHeightPreference??min,min,max);
      input.style.setProperty('--room-input-height',height+'px');input.style.height=height+'px';return;
    }
    input.style.removeProperty('--room-input-height');input.style.height = 'auto';
    input.style.height = Math.min(160, Math.max(52, input.scrollHeight))+'px';
  }
  function inCode(text) {
    let fence = null, ticks = '';
    for (const line of text.split('\n')) {
      const delimiter = line.match(/^\s{0,3}(`{3,}|~{3,})(.*)$/);
      if (delimiter && !ticks) {
        if (!fence) fence = delimiter[1];
        else if (delimiter[1][0] === fence[0] && delimiter[1].length >= fence.length && !delimiter[2].trim()) fence = null;
        continue;
      }
      if (fence) continue;
      if (/^(?: {4}|\t)/.test(line)) { ticks = 'indented'; continue; }
      if (ticks === 'indented') ticks = '';
      for (const match of line.matchAll(/`+/g)) {
        if (!ticks) ticks = match[0];
        else if (ticks === match[0]) ticks = '';
      }
    }
    return !!(fence || ticks);
  }
  function initMentions() {
    const input = $('#room-text');
    const list = node('ul','room-mentions'); list.id = 'room-mentions'; list.hidden = true;
    list.setAttribute('role','listbox'); list.setAttribute('aria-label','提及成员');
    input.closest('.room-input-wrap').append(list);
    input.setAttribute('role','combobox'); input.setAttribute('aria-autocomplete','list');
    input.setAttribute('aria-haspopup','listbox'); input.setAttribute('aria-controls',list.id);
    input.setAttribute('aria-expanded','false'); input.setAttribute('aria-multiline','true');
    let context = null, choices = [], active = 0;
    function close() {
      list.hidden = true; context = null;
      input.setAttribute('aria-expanded','false'); input.removeAttribute('aria-activedescendant');
    }
    function selectActive() {
      Array.from(list.children).forEach((option,i) => option.setAttribute('aria-selected',String(i === active)));
      input.setAttribute('aria-activedescendant',list.children[active].id);
    }
    function refresh() {
      const end = input.selectionStart, before = input.value.slice(0,end);
      const match = before.match(/(?:^|[^\w@./:+%\-])@([a-z0-9_\u3400-\u9fff]*)$/i);
      if (document.activeElement !== input || input.selectionEnd !== end || !match || inCode(before)) { close(); return; }
      choices = BoardIdentity.accounts.map(a => a.id).filter(name => name.toLowerCase().startsWith(match[1].toLowerCase()));
      if (!choices.length) { close(); return; }
      context = {start:end-match[1].length-1,end}; active = 0; list.replaceChildren();
      choices.forEach((name,i) => {
        const option = node('li','room-mention-option','@'+name);
        option.id = 'room-mention-'+name; option.setAttribute('role','option');
        option.addEventListener('pointerdown',event => event.preventDefault());
        option.onclick = () => choose(i); list.append(option);
      });
      list.hidden = false; input.setAttribute('aria-expanded','true'); selectActive();
    }
    function choose(index) {
      if (!context) return;
      const {start,end} = context, value = '@'+choices[index]+' ';
      if (input.maxLength > 0 && input.value.length-(end-start)+value.length > input.maxLength) { close(); return; }
      input.focus({preventScroll:true}); input.setSelectionRange(start,end);
      // Native insertText keeps the textarea's undo history, including typed drafts.
      const inserted = document.execCommand('insertText',false,value);
      if (!inserted) { input.setRangeText(value,start,end,'end'); input.dispatchEvent(new Event('input',{bubbles:true})); }
      close();
    }
    input.addEventListener('input',event => { if (event.isComposing) close(); else refresh(); });
    input.addEventListener('compositionstart',close); input.addEventListener('compositionend',refresh);
    input.addEventListener('click',refresh); input.addEventListener('select',() => { if (!list.hidden) refresh(); });
    input.addEventListener('keyup',event => { if (['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) refresh(); });
    input.addEventListener('blur',close);
    input.addEventListener('keydown',event => {
      if (event.isComposing || event.keyCode === 229 || list.hidden) return;
      if (event.key === 'Escape') { event.preventDefault(); close(); return; }
      if (event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) { if (event.key === 'Enter') close(); return; }
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault(); active = (active+(event.key === 'ArrowDown' ? 1 : choices.length-1))%choices.length; selectActive();
      } else if (event.key === 'Enter') { event.preventDefault(); choose(active); }
    });
  }
  function reply(item) {
    if(typeof RoomExtras==='object'&&(RoomExtras.readOnly()||item.deleted))return;
    draft.parent_id = item.id; draft.client_id = null; save(); composer();
    $('#room-text').focus({preventScroll:true});
  }
  function jumpTo(id, auto = false) {
    const target = Array.from($('#room-threads').children).find(item => item.dataset.discussionId === id);
    if (!target) {
      const index = items.findIndex(item => item.id === id);
      const needed = index < 0 ? 0 : items.length - index + 6;
      if (needed > limit && (!auto || needed <= 120)) {
        limit = needed;
        render({target:id, auto});
      } else if (auto) scrollLatest(false);
      return;
    }
    const log = $('#room-threads'); log.scrollTop = target.offsetTop - log.offsetTop - 20;
    target.classList.remove('room-highlight'); void target.offsetWidth; target.classList.add('room-highlight');
  }
  function message(item, byId) {
    item=RoomExtras.projectDeleted(item);
    const name = item.author || '协作记录', mine = name === BoardIdentity.me.id;
    const article = node('article', 'room-message by-'+String(name).toLowerCase()+(mine ? ' mine' : ''));
    article.dataset.discussionId = item.id;
    const avatar = node(avatars[name] ? 'button' : 'span', 'room-avatar '+name.toLowerCase(), name === 'owner' ? 'T' : name === 'Claude' ? 'C' : name === 'GPT' ? 'G' : '·');
    if (avatars[name]) avatar.type = 'button';
    else avatar.setAttribute('aria-hidden','true');
    decorateAvatar(avatar, name);
    const content = node('div','room-message-content'), meta = node('div','room-meta');
    meta.append(node('span','room-author',BoardIdentity.name(name)));
    if(item.source_label)meta.append(node('span','room-source-label',item.source_label));
    const time = node('time',null,String(item.created_at || '').slice(11,16));
    time.dateTime = item.created_at || ''; time.title = String(item.created_at || '').replace('T',' ').slice(0,16); meta.append(time);
    const bubble = node('div','room-bubble');
    if(item.deleted){
      article.classList.add('room-message-deleted');article.tabIndex=-1;
      bubble.append(node('p','room-deleted-marker',RoomExtras.deletionText(item)));
      content.append(meta,bubble);article.append(avatar,content);return article;
    }
    if (item.parent_id || item.parent_deleted) {
      const parent = byId.get(item.parent_id), quote = node('button','room-quote'); quote.type = 'button';
      const gone=item.parent_deleted===true||parent?.deleted;
      quote.append(node('span','room-quote-author',gone ? '回复' : parent ? BoardIdentity.name(parent.author) : '回复'),node('span',null,gone ? '原消息已撤回' : parent ? excerpt(parent.body) : '查看原消息'));
      quote.setAttribute('aria-label','查看回复的原消息');quote.disabled=!item.parent_id;quote.onclick = () => {if(item.parent_id)jumpTo(item.parent_id);};bubble.append(quote);
    }
    const text = String(item.body || ''), long = text.length > 700, open = expanded.has(item.id);
    if (text) {
      const body = RoomMarkdown.render(long && !open ? text.slice(0,480)+'…' : text,markdownOptions());
      if (body.querySelector('.room-mention-self')) article.classList.add('room-mentioned');
      bubble.append(body);
    }
    if ((item.images || []).length) {
      const box=node('div','room-images');
      item.images.forEach((name,index) => {
        const url=RoomExtras.mediaURL(name); if(!url)return;
        const button=node('button');button.type='button';button.setAttribute('aria-label','查看图片 '+(index+1));
        const img=node('img');img.src=url;img.alt='消息图片 '+(index+1);img.loading='lazy';
        button.onclick=()=>RoomExtras.gallery(item,index,button);button.append(img);box.append(button);
      });
      bubble.append(box);
    }
    if(item.sticker && RoomExtras.stickerURL(item.sticker.id,item.sticker.url)) {
      const img=node('img','room-sticker');img.src=RoomExtras.stickerURL(item.sticker.id);img.alt=item.sticker.label;img.loading='lazy';bubble.append(img);
    }
    if (long) {
      const more = node('button','room-expand',open ? '收起' : '展开全文'); more.type = 'button'; more.setAttribute('aria-expanded',String(open));
      more.onclick = () => { if (expanded.has(item.id)) expanded.delete(item.id); else expanded.add(item.id); render(); };
      bubble.append(more);
    }
    const footer = node('div','room-foot'), button = node('button','room-reply-button','回复');
    button.type = 'button'; button.setAttribute('aria-label','回复'+BoardIdentity.name(name)+'的发言'); button.onclick = () => reply(item); if(!RoomExtras.readOnly())footer.append(button);
    footer.append(reactionControls(item));
    const actions=RoomExtras.messageActions(item,article,{reply:()=>reply(item),failed:message=>status(message,true),deleted:changed=>{
      items=items.map(current=>current.id===item.id?changed:current);lastRevision='';
      RoomExtras.messageDeleted?.(item.id);render();
      Array.from($('#room-threads').children).find(row=>row.dataset.discussionId===item.id)?.focus({preventScroll:true});
      status(changed.delete_action==='delete'?'消息已删除':'消息已撤回');
    }});if(actions)footer.append(actions);
    if(BoardIdentity.me.conversations){
      if(item.reference){const ref=node('button','room-reference',byId.get(item.reference.message_id)?.deleted||item.reference.deleted?'原消息已撤回':'查看来源');ref.type='button';ref.onclick=()=>jumpTo(item.reference.message_id);bubble.prepend(ref);}
      for(const file of item.files||[])bubble.append(RoomExtras.fileLink(file));
    }
    article.setAttribute('aria-label',BoardIdentity.name(name)+(item.source_label?' · '+item.source_label:'')+' · '+String(item.created_at || ''));
    content.append(meta,bubble,footer); article.append(avatar,content); return article;
  }
  function reactionControls(item) {
    const controls=RoomExtras.reactions(item,reactionEmoji,result=>{
      const current=items.find(message=>message.id===item.id);if(!current)return;current.reactions=result.reactions;
      const target=Array.from($('#room-threads').children).find(article=>article.dataset.discussionId===item.id)?.querySelector('.room-reactions');
      const next=reactionControls(current);target?.replaceWith(next);next.querySelector('button')?.focus({preventScroll:true});
    },message=>status(message,true));
    return controls;
  }
  function latestLabel() {
    const count=reader?.unread.size || 0;
    $('#room-latest').textContent='↓ 回到最新消息'+(count?' · '+count+' 条未读':'');
    $('#room-latest').hidden=atBottom() && !count;
  }
  function atBottom() { const log = $('#room-threads'); return log.scrollHeight-log.scrollTop-log.clientHeight < 72; }
  function scrollLatest(acknowledge=true) { const log=$('#room-threads');log.scrollTop=log.scrollHeight;if(acknowledge && RoomExtras.visible(log))reader?.mark();latestLabel(); }
  function render(options = {}) {
    RoomExtras.closeMenus();
    const log = $('#room-threads'), before = log.scrollHeight, position = log.scrollTop, nearBottom = atBottom();
    const active = document.activeElement, focusedId = active?.closest('.room-message')?.dataset.discussionId;
    const restoreExpandFocus = active?.classList.contains('room-expand');
    const anchor = Array.from(log.children).find(item => item.dataset.discussionId && item.offsetTop+item.offsetHeight >= log.offsetTop+position);
    const anchorId = anchor?.dataset.discussionId, anchorOffset = anchor ? anchor.offsetTop-log.offsetTop-position : 0;
    if (!options.older && !options.target && (options.forceBottom || nearBottom)) limit = Math.min(limit, 18);
    const byId = new Map(items.map(item => [item.id,item])), selected = items.slice(-limit);
    log.replaceChildren();
    if (items.length > selected.length) {
      const history = node('button','room-history','查看更早的消息'); history.type = 'button'; history.id = 'room-more';
      history.onclick = () => { limit += 24; render({older:true}); }; log.append(history);
    }
    if (!selected.length) log.append(node('div','room-empty','从你的第一句话开始聊。'));
    let day = '', previous = null;
    selected.forEach(item => {
      const date = String(item.created_at || '').slice(0,10);
      if (date && date !== day) {
        const separator = node('div','room-date'); separator.append(node('span',null,date.replace(/-/g,' / '))); log.append(separator); day = date;
      }
      if (item.id===reader?.boundary) {
        const divider=node('div','room-unread-divider','以下为新消息');divider.setAttribute('role','separator');log.append(divider);
      }
      const article=message(item,byId);
      if(RoomExtras.merge(previous,item,reader?.boundary)){
        article.classList.add('room-continuation');const avatar=article.querySelector('.room-avatar');avatar.tabIndex=-1;avatar.setAttribute('aria-hidden','true');
      }
      log.append(article);previous=item;
    });
    composer();
    if (options.target) jumpTo(options.target, options.auto);
    else if (options.older) log.scrollTop = position+log.scrollHeight-before;
    else if (options.forceBottom || nearBottom || !before) scrollLatest(false);
    else {
      const same = Array.from(log.children).find(item => item.dataset.discussionId === anchorId);
      log.scrollTop = same ? same.offsetTop-log.offsetTop-anchorOffset : position;
      $('#room-latest').hidden = false;
    }
    latestLabel();
    if (restoreExpandFocus) Array.from(log.children).find(item => item.dataset.discussionId === focusedId)?.querySelector('.room-expand')?.focus({preventScroll:true});
    else if(byId.get(focusedId)?.deleted)Array.from(log.children).find(item=>item.dataset.discussionId===focusedId)?.focus({preventScroll:true});
  }
  function update(data) {
    syncAvatars();

    if(data && (data.channel||'main')!==BoardIdentity.channel)return;
    if (!data || data.revision === lastRevision) return;
    const firstLoad=!items.length, readNow=items.length>0 && atBottom() && RoomExtras.visible($('#room-threads'));
    lastRevision=data.revision;items=RoomExtras.discussionItems(data.items).slice().sort((a,b)=>(Date.parse(a.created_at)||0)-(Date.parse(b.created_at)||0));
    for(const item of items)if(item.deleted)RoomExtras.messageDeleted?.(item.id);
    reader?.sync(items);if(readNow)reader?.mark();
    reactionEmoji=data.reaction_emoji || reactionEmoji;
    RoomExtras.setReactionCatalog?.(data.reaction_catalog || []);
    render(firstLoad && reader?.unread.size ? {target:reader.boundary, auto:true} : {});
  }
  function showPending() {
    const box = $('#room-attach'); box.replaceChildren(); box.hidden = !pending.length;
    pending.forEach((p, i) => { const t = node('div','thumb'), img = node(/^image\//.test(p.file.type)?'img':'span'), x = node('button',null,'×');
      if(img.tagName==='IMG'){img.src=p.url;img.alt='待发送的图片';}else img.textContent=p.file.name; x.type = 'button'; x.setAttribute('aria-label','移除这张图片');
      x.onclick = () => { URL.revokeObjectURL(p.url); pending.splice(i,1); showPending(); }; t.append(img,x); box.append(t); });
  }
  function addFiles(files) {
    if(RoomExtras.readOnly())return;
    for (const f of files) {
      if (!/^image\/(png|jpeg|webp|gif)$/.test(f.type) && (!BoardIdentity.me.conversations || !/\.(pdf|txt|md|csv|json|docx|xlsx|pptx|zip|html)$/i.test(f.name))) { status('请选择图片、文档或压缩包。',true); continue; }
      if (f.size > 8*1024*1024) { status('图片太大了，每张请控制在 8 MB 以内。',true); continue; }
      if (pending.length >= 6) { status('一次最多发 6 张图片。',true); break; }
      pending.push({file:f, url:URL.createObjectURL(f)});
    }
    showPending(); draft.client_id = null;
  }
  const asDataUrl = f => new Promise((ok, bad) => { const r = new FileReader(); r.onload = () => ok(r.result); r.onerror = bad; r.readAsDataURL(f); });
  async function submit(event) {
    event.preventDefault(); if (sending||RoomExtras.readOnly()) return;
    const body = $('#room-text').value.trim();
    if (!body && !pending.length) { status('写点内容或放张图片再发送。',true); $('#room-text').focus(); return; }
    if(draft.client_id && draft.retry_actor && draft.retry_actor!==BoardIdentity.me.id){
      status('这条消息以'+BoardIdentity.name(draft.retry_actor)+'发送，请切回该身份后重试。',true);return;
    }
    const retryActor=draft.client_id?draft.retry_actor:null;
    draft.body = body; if (!draft.client_id) draft.client_id = crypto.randomUUID(); save(); sending = true;
    const submission={body,parent_id:draft.parent_id || null,client_id:draft.client_id};
    $('#room-submit').disabled = $('#room-text').disabled = $('#room-cancel').disabled = true; status('正在发送…');
    try {
      const images=await Promise.all(pending.filter(p=>/^image\//.test(p.file.type)).map(p=>asDataUrl(p.file)));
      const files=await Promise.all(pending.filter(p=>!/^image\//.test(p.file.type)).map(async p=>({name:p.file.name,data:await asDataUrl(p.file)})));
      if(retryActor && retryActor!==BoardIdentity.me.id)throw new Error('这条消息以'+BoardIdentity.name(retryActor)+'发送，请切回该身份后重试。');
      submission.images=images;if(BoardIdentity.me.conversations)submission.files=files;submission.author=BoardIdentity.me.id;submission.channel=BoardIdentity.channel;
      draft.retry_actor=submission.author;save();
      const response = await fetch('/api/discussion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(submission)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || '发送遇到问题，草稿已保留。');
      draft = {body:'',parent_id:null}; save(); $('#room-text').value = ''; resizeInput(); composer(); status('已发送');
      pending.forEach(p => URL.revokeObjectURL(p.url)); pending = [], inputHeightPreference=null; showPending();
      if (!items.some(item => item.id === data.post.id)) items.push(data.post);
      lastRevision = '';reader?.sync(items);reader?.mark();render({forceBottom:true});
      try { const board = await (await fetch('/api/board',{cache:'no-store'})).json(); if(submission.channel===BoardIdentity.channel)update((await (await fetch('/api/discussion')).json())); } catch (_) {}
    } catch (error) { status(error.message || '连接遇到问题，草稿已保留。',true); }
    finally { sending = false; $('#room-submit').disabled = $('#room-text').disabled = $('#room-cancel').disabled = false; $('#room-text').focus({preventScroll:true}); }
  }
  function alignMessagesWithIdentity() {
    const authors=new Map(items.map(item=>[item.id,item.author]));
    for(const article of $('#room-threads').children){
      if(authors.has(article.dataset.discussionId))article.classList.toggle('mine',authors.get(article.dataset.discussionId)===BoardIdentity.me.id);
    }
  }
  function init() {
    reader=RoomExtras.reader(BoardIdentity.me.id,BoardIdentity.channel);
    restoreDraft();
    syncAvatars();
    window.addEventListener('accountschange', () => { syncAvatars(); render(); });
    window.addEventListener('identitychange', () => {
      save();syncAvatars();composer();alignMessagesWithIdentity();
      RoomExtras.closeMenus();items=items.map(item=>({...item,can_delete:false}));render();lastRevision='';
      fetch('/api/discussion',{cache:'no-store'}).then(response=>response.ok?response.json():null).then(data=>data&&update(data)).catch(()=>{});
    });
    window.addEventListener('boardchannel', () => { save();channelPending.set(pendingChannel,pending);pendingChannel=BoardIdentity.channel;pending=channelPending.get(pendingChannel)||[];restoreDraft();reader=RoomExtras.reader(BoardIdentity.me.id,BoardIdentity.channel);$('#room-text').value=draft.body;showPending();items=[];lastRevision='';render();composer(); });
    const members = document.querySelector('.room-members');
    members?.removeAttribute('aria-hidden');
    members?.querySelectorAll('.room-avatar').forEach(avatar => {
      const name = Object.keys(avatars).find(name => avatar.classList.contains(name.toLowerCase()));
      if (name) {
        const button = node('button',avatar.className,avatar.textContent); button.type = 'button';
        avatar.replaceWith(button); decorateAvatar(button, name);
      }
    });
    $('#room-text').value = draft.body; resizeInput();
    initMentions();
    $('#room-form').addEventListener('submit',submit);
    $('#room-text').addEventListener('input',() => { draft.body = $('#room-text').value; draft.client_id = null;delete draft.retry_actor; save(); resizeInput(); status(draft.body ? '草稿已保存' : ''); });
    $('#room-text').addEventListener('keydown',event => {
      if (event.key === 'Enter' && !event.shiftKey && !event.altKey && !event.isComposing && event.keyCode !== 229 && !event.defaultPrevented) {
        event.preventDefault(); $('#room-form').requestSubmit();
      }
    });
    const hint = document.querySelector('.room-composer-hint');
    if (hint) hint.textContent = 'Enter 发送 · Shift+Enter 换行';
    $('#room-cancel').onclick = () => { draft.parent_id = null; draft.client_id = null; save(); composer(); };
    const attach = node('div','room-attach'); attach.id = 'room-attach'; attach.hidden = true;
    $('#room-text').closest('.room-input-wrap').before(attach);
    const picker = node('input'); picker.type = 'file'; picker.accept = 'image/png,image/jpeg,image/webp,image/gif,.pdf,.txt,.md,.csv,.json,.docx,.xlsx,.pptx,.zip,.html'; picker.multiple = true; picker.hidden = true;
    const pick = node('button','room-pick',BoardIdentity.me.conversations?'＋ 附件':'＋ 图片'); pick.type = 'button'; pick.title = '也可以直接粘贴或拖进来';
    pick.onclick = () => picker.click(); picker.onchange = () => { addFiles(picker.files); picker.value = ''; };
    $('#room-submit').before(pick, picker);
    $('#room-text').addEventListener('paste', e => { const fs = Array.from(e.clipboardData?.files || []).filter(f => f.type.startsWith('image/')); if (fs.length) { e.preventDefault(); addFiles(fs); } });
    const form = $('#room-form');
    form.addEventListener('dragover', e => { if (Array.from(e.dataTransfer?.types || []).includes('Files')) { e.preventDefault(); form.classList.add('room-drop'); } });
    form.addEventListener('dragleave', () => form.classList.remove('room-drop'));
    form.addEventListener('drop', e => { form.classList.remove('room-drop'); const fs = Array.from(e.dataTransfer?.files || []); if (fs.length) { e.preventDefault(); addFiles(fs); } });
    $('#room-latest').onclick = scrollLatest;
    if(RoomExtras.readOnly()){
      for(const control of [$('#room-text'),$('#room-submit'),$('#room-cancel'),pick,picker])control.disabled=true;
      pick.hidden=true;status('访客只读');
    }
    const markVisible=()=>{if(atBottom() && RoomExtras.visible($('#room-threads')))reader.mark();latestLabel();};
    $('#room-threads').addEventListener('scroll',markVisible,{passive:true});
    document.addEventListener('visibilitychange',markVisible);
    new MutationObserver(markVisible).observe($('#msgs'),{attributes:true,attributeFilter:['class']});
    composer();
    initSizing();

  }
  return {init,update,cleanText,jumpTo,sizing};
})();
