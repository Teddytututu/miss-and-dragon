/* Presentation-only language switching. Stored project records keep their original text. */
((root) => {
  'use strict';
  const english = {
    "新":"New",
    "改过":"Updated",
    "只看未读":"Unread only",
    "这些结果都看过了。":"All results read.",
    "这项结果有新内容":"This result has new content",
    "📄 结果页":"📄 Report",
    "页面连接中":"Connecting to report",
    "← 起因：":"← Cause ",
    "引出 →：":"Leads to → ",
    "看链条":"View chain",
    "收起链条":"Clear chain",
    "调节侧栏宽度":"Resize detail panel",
    "左右拖动调宽，双击恢复默认，方向键微调":"Drag to resize, double-click to reset, arrow keys to adjust",
    "成员资料":"Member profiles",
    "便利贴操作":"Note actions",
    "回一句":"Reply",
    "✎ 回一句":"✎ Reply",
    "放进今天":"Add to Today",
    "拖进今天":"Drag to Today",
    "写一句…":"Write a reply…",
    "最多40字":"Up to 40 characters",
    "昨天没做":"Carried over",
    "待排":"Unscheduled",
    "已放进今天，等助手排时间。":"Added to Today for scheduling.",
    "请重试保存。":"Try saving again.",
    '告诉 Claude 你的研究问题和想要的成果':'Tell Miss your research question and desired deliverable','在讨论室告诉大小姐':'Tell Miss in the discussion room','使用固定巡检间隔':'Using a fixed patrol interval',
    '跳到正文':'Skip to content','研究工作台':'Research desk','需要你做的':'Your actions',
    '你的安排':'Your schedule','研究进度':'Research progress','报告与文件':'Reports & files',
    '正在做':'In progress','协作额度':'Agent capacity','研究目标':'Research goal',
    '一句研究问题':'Research question','想要的成果':'Desired deliverable','你的显示名':'Your display name',
    '保存项目':'Save project','你的消息':'Your message','取消回复':'Cancel reply',
    'Shift + Enter 发送':'Shift + Enter to send','Enter 发送 · Shift+Enter 换行':'Enter to send · Shift+Enter for a new line',
    'Claude 负责研究设计与审核，GPT 负责实现与实验。讨论室里的开工消息由助手在实际会话中发送；示例与历史初始化说明分别标明。':
      'Claude designs and reviews the research; GPT implements and runs experiments. Each assistant posts from its own session. Demo and historical setup messages are labelled.',
    '现在没有要你做的事。':'You have no actions right now.','今天没有排具体安排。':'No specific plans for today.',
    '现在':'Now','今天':'Today','明天':'Tomorrow','后面的安排':'Upcoming plans',
    '正在跑的实验':'Running experiments','已跑完的实验（':'Completed experiments (',
    'DraCo 复现与判分':'DraCo reproduction & evaluation','提前读出':'Early readout','修改与回退':'Changes & rollback',
    '文献与代码':'Papers & code','界面与设计':'Interface & design','视频':'Video','其他':'Other',
    '已完成':'Completed','进行中':'In progress','待做':'To do','有效':'Effective','一般':'Mixed',
    '有短板':'Needs improvement','结论':'Conclusion','放大查看':'Enlarge ','图片':'Image',
    '相关的活':'Related tasks',' 组结果':' result sets',' 个活':' tasks','全部展开':'Expand all',
    '全部收起':'Collapse all','展开全文':'Read full message','展开':'Expand','收起':'Collapse',
    '目标':'Goal','交付':'Deliverable','前置任务':'Prerequisites','等条件 · ':'Waiting · ',
    '这一轮任务已交齐。':'All tasks in this round have been delivered.','网址':'URL','网页':'Web',
    '文档':'Document','文件夹':'Folder','已在资源管理器打开':'Opened in the file manager',
    '已打开':'Opened','只能在电脑上打开':'Open this on your computer','找不到这个文件':'File not found',
    '打开失败':'Could not open the file','复制路径':'Copy path','路径已复制':'Path copied',
    '研究':'Research','学习':'Study','事务':'Admin','项目':'Project','综合':'General',
    '没有匹配的报告与文件':'No matching reports or files','还没有报告与文件':'No reports or files yet',
    '已处理的报告与文件（':'Archived reports & files (','讨论室':'Discussion','收起讨论室':'Collapse discussion',
    '拖动调宽度':'Drag to resize','这么晚还没睡？':'Working late?','早安呀':'Good morning',
    '中午好呀':'Good afternoon','下午好呀':'Good afternoon','晚上好呀':'Good evening','研究协作':'Research collaboration',
    ' 件事等你':' actions for you','关闭头像大图':'Close avatar preview','关闭':'Close',
    '图片正在准备，请稍后再试。':'The image is getting ready. Try again shortly.',
    '头像图片加载遇到问题，请稍后重试。':'The avatar could not load. Try again shortly.',
    '的头像大图':' — full avatar','的头像':' — avatar','头像大图':'Full avatar','Claude头像':'Claude avatar',
    '头像':'Avatar','发言者：':'Posting as: ',' 位成员':' members','页面风格':'Theme','蓝色':'Blue','粉色':'Pink',
    '原消息已撤回':'Original message withdrawn','回复所选消息':'Reply to selected message','发送回复':'Send reply',
    '提及成员':'Mention a member','协作记录':'Collaboration record','查看回复的原消息':'View the original message',
    '查看原消息':'View original message','查看来源':'View source','查看图片 ':'View image ',
    '消息图片 ':'Message image ','的发言':' — message','消息已删除':'Message deleted','消息已撤回':'Message withdrawn',
    '↓ 回到最新消息':'↓ Latest messages',' 条未读':' unread','查看更早的消息':'Load earlier messages',
    '从你的第一句话开始聊。':'Start the conversation with your first message.','以下为新消息':'New messages',
    '待发送的图片':'Image attachment','移除这张图片':'Remove image','请选择图片、文档或压缩包。':'Choose an image, document or archive.',
    '图片太大了，每张请控制在 8 MB 以内。':'Each image can be up to 8 MB.','一次最多发 6 张图片。':'Send up to 6 images at a time.',
    '写点内容或放张图片再发送。':'Add a message or image before sending.','这条消息以':'This message belongs to ',
    '发送，请切回该身份后重试。':'. Switch back to that identity to send it.',
    '正在发送…':'Sending…','发送遇到问题，草稿已保留。':'Sending failed. Your draft is saved.',
    '连接遇到问题，草稿已保留。':'Connection problem. Your draft is saved.','已发送':'Sent','草稿已保存':'Draft saved',
    '＋ 附件':'＋ Attach','＋ 图片':'＋ Image','也可以直接粘贴或拖进来':'You can also paste or drop a file here',
    '访客只读':'Read-only guest','请稍后重试。':'Try again shortly.','管理员':'Administrator',
    ' 删除了一条消息':' deleted a message',' 撤回了一条消息':' withdrew a message',
    '这条消息？':' this message?','消息位置将显示':'The message will show a ',
    '标记。':' marker.','保留消息':'Keep message','消息操作':'Message actions','管理员删除':'Deleted by administrator',
    '消息状态更新中，请稍后重试。':'Message status is updating. Try again shortly.',
    '回应成员':'People who reacted','另有 ':'Plus ',' 次历史回应':' historical reactions',
    '完成':'Done','关心':'Care','微笑':'Smile','庆祝':'Celebrate','审阅':'Review','想法':'Idea',
    ' 人回应':' reactions','，点击取消自己的回应':'; click to remove your reaction','＋ 表情':'＋ React',
    '选择表情回应':'Choose a reaction','选择表情':'Choose an emoji','表情':'Emoji','返回':'Back',
    '消息图片全屏查看':'Full-screen message image','图片加载遇到问题，请稍后重试。':'The image could not load. Try again shortly.',
    '上一张图片':'Previous image','下一张图片':'Next image','请稍后重试，草稿已保留。':'Try again shortly. Your draft is saved.',
    '提及 ':'Mention ','查看私聊图片 ':'View private image ','私聊图片 ':'Private image ',
    '还没有消息':'No messages yet','加载遇到问题，请点击刷新。':'Loading failed. Select refresh to try again.',
    '查看更早留言':'Load earlier messages','刷新':'Refresh','记录':'Records','正在加载…':'Loading…',
    '我的私聊':'My private chats','返回讨论室':'Back to discussion','选择私聊对象':'Choose a private chat',
    '给 GPT 的私聊消息':'Private message to GPT','也可以粘贴或拖入图片':'You can also paste or drop images',
    '移除这份附件':'Remove attachment','图片请使用 PNG、JPG、WebP、GIF。':'Use PNG, JPG, WebP or GIF images.',
    '图片请控制在 8 MiB 以内。':'Each image can be up to 8 MiB.','图片读取遇到问题，草稿已保留。':'The image could not be read. Your draft is saved.',
    '已发送给 ':'Sent to ','正在发送给 ':'Sending to ','，请稍候。':' — please wait.',
    ' 的私聊消息':' — private message',' 发消息…':' — write a message…','私聊图片全屏查看':'Full-screen private image',
    '私聊 ':'Private chat ',' 私聊':' — private chat','私聊':'Private chat','文件分类':'File categories',
    '全部':'All','课程筛选':'Filter courses','分钟':' min','小时':' hr','本阶段已完成':'Current stage complete',
    '随实验队列交付':'Delivered with the experiment queue','已暂停，恢复后约':'Paused; about ',
    '已暂停，条件恢复后更新':'Paused; updates when conditions recover','前置条件明确':'prerequisites confirmed',
    '后约':'; then about ','后更新':'; updates afterward','预计时间待更新':'ETA awaiting update','预计待定':'ETA pending',
    '已超时 · ':'Overdue · ','预计 ':'Expected ','把握：':'Confidence: ','上一轮交付':'Previous delivery',
    '收图':'Image return','等登录':'Waiting for login','等空卡':'Waiting for a GPU','等领取':'Waiting for assignment',
    '约 ':'About ','明早 ':'Tomorrow morning ','明天 ':'Tomorrow ','已停':'Stopped','暂停':'Paused',
    ' 交':' delivery','每日':'Daily','卡住':'Blocked','在跑':'Running','排队':'Queued',
    '巡检超时':'Patrol overdue','已巡检':'Patrol recorded','待巡检':'Patrol pending','助手巡检':'Agent patrols',
    '待登记':'Awaiting record','上次 ':'Last ',' · 下次 ':' · Next ','流程问题 ':'Flow issues ',
    '登记巡检后显示摘要':'A summary appears after a patrol is recorded','充足':'Available','紧张':'Low','见底':'Almost empty',
    '原生观测 · ':'Observed · ','手动估计 · 约':'Manual estimate · about ','档位估计 · 约':'Band estimate · about ',
    '上报估计 · 约':'Reported estimate · about ','保守上界 · ':'Conservative upper bound · ',
    '原生限制':'Provider limit','待上报':'Awaiting report','原生观测额度':'Observed capacity','额度估计':'Capacity estimate',
    '提及或验收时唤醒':'Wake for mentions or review','待计算':'Awaiting calculation','巡检建议待上报':'Patrol advice awaiting report',
    '建议巡检 · ':'Suggested patrol · ','初始档位仅用于规划；助手上报后更新。':'Initial bands guide planning; agents update them when reporting.',
    '观测时间 · ':'Observed at · ','手动估计档位 ':'Manual estimate band ','额度档位':'Capacity band',
    '选择档位':'Choose a band','初始估计分工 ':'Initial estimated workload ','建议分工 ':'Suggested workload ',
    '已保存':'Saved','筛选报告与文件':'Filter reports and files','筛选…':'Filter…','聊天消息':'Chat messages',
    '说点什么，大家一起聊…':'Write a message…','发送消息':'Send message','发送':'Send','回复 ':'Reply to ',
    '回复':'Reply','确认':'Confirm','删除':'Delete','撤回':'Withdraw','消息':'Message','待办':'Actions',
    '安排':'Schedule','进度':'Progress','结果':'Results','在做':'Tasks','文件':'Files','已交':'Delivered',
    '示例':'Demo','复习':'Revision','实验':'Experiment','考试':'Exam','你好呀':'Hello',
    '手动估计档位':'Manual estimate band',
    '低':'Low','等':'Waiting for ','查看':'View '
  };
  const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // Match once against the original text, so English output is never translated again.
  const pattern = new RegExp(Object.keys(english).sort((a,b)=>b.length-a.length).map(escape).join('|'),'g');
  function translate(text, language='en') {
    if(language!=='en' || typeof text!=='string')return text;
    if(Object.hasOwn(english,text))return english[text];
    const trimmed=text.trim();
    if(Object.hasOwn(english,trimmed))return text.replace(trimmed,english[trimmed]);
    const greeting=trimmed.match(/^(.*)，(这么晚还没睡？|早安呀|中午好呀|下午好呀|晚上好呀)$/);
    if(greeting)return greeting[1]+', '+english[greeting[2]];
    const day=trimmed.match(/^(\d+) 月 (\d+) 日 · 周([日一二三四五六]) · 有 (\d+) 件事等你$/);
    if(day)return `${day[1]}/${day[2]} · ${['Sun','Mon','Tue','Wed','Thu','Fri','Sat']['日一二三四五六'.indexOf(day[3])]} · ${day[4]} actions for you`;
    // Only known generated captions may contain variable names, dates or counts.
    // Unknown sentences, category names and project records retain their wording.
    if(!/^(?:\d+\s*(?:位成员|条未读|人回应|分钟|小时|个活|组结果)|(?:今天|明天|等条件) · |已跑完的实验（|已处理的报告与文件（|发言者：|↓ 回到最新消息|(?:查看|回复|提及).+(?:头像|的发言|图片)|(?:已发送给|正在发送给|私聊 |建议巡检 · |观测时间 · |建议分工 |初始估计分工 |手动估计档位 |原生观测 · |手动估计 · 约|档位估计 · 约|上报估计 · 约|保守上界 · |上次 |流程问题 |预计 |已超时 · |约 |明早 )|.+(?:的头像(?:大图)?|额度档位)$)/.test(trimmed))return text;
    return text.replace(pattern, value=>english[value]).replace(/（/g,' (').replace(/）/g,')');
  }
  if(typeof module==='object' && module.exports)module.exports={translate};
  if(!root.document)return;
  const document=root.document, texts=new WeakMap(), attributes=new WeakMap();
  const excluded='script,style,pre,code,[contenteditable],#language-switch,[data-no-i18n],#nav .brand small,h1.sr-only,.room-bubble,.room-markdown,.room-author,#room-reply-label,.private-bubble,.private-text,.todo-what,.todo-how,.todo-item .muted,.slot .w,#lines,.rcname,.rxname,.rxtake,.dsummary,.nd>span:not(.st):not(.cnt),.n,.tt-title,.fname,figcaption';
  let language='zh-CN', queued=false;
  try{language=new URL(root.location.href).searchParams.get('lang') || root.localStorage.getItem('md-language') || language;}catch(_){}
  if(!['en','zh-CN'].includes(language))language='zh-CN';
  function apply() {
    queued=false;
    if(!document.body)return;
    const walker=document.createTreeWalker(document.body,root.NodeFilter.SHOW_TEXT);
    for(let node;(node=walker.nextNode());){
      const parent=node.parentElement;if(!parent || parent.closest(excluded+',textarea,input'))continue;
      const prior=texts.get(node), original=prior && node.data===prior.rendered?prior.original:node.data;
      const rendered=translate(original,language);texts.set(node,{original,rendered});
      if(node.data!==rendered)node.data=rendered;
    }
    for(const element of document.body.querySelectorAll('[title],[placeholder],[aria-label]')){
      if(element.closest(excluded))continue;
      const memory=attributes.get(element)||{};
      for(const name of ['title','placeholder','aria-label']){
        if(!element.hasAttribute(name))continue;
        const current=element.getAttribute(name),prior=memory[name];
        const original=prior && prior.rendered===current?prior.original:current;
        const rendered=translate(original,language);memory[name]={original,rendered};
        if(current!==rendered)element.setAttribute(name,rendered);
      }
      attributes.set(element,memory);
    }
    document.documentElement.lang=language;
  }
  function schedule(){if(!queued){queued=true;queueMicrotask(apply);}}
  function setLanguage(value){
    if(!['en','zh-CN'].includes(value))return;
    language=value;
    try{root.localStorage.setItem('md-language',value);}catch(_){}
    try{const url=new URL(root.location.href);url.searchParams.set('lang',value);root.history.replaceState(null,'',url);}catch(_){}
    apply();root.dispatchEvent(new CustomEvent('languagechange',{detail:{language}}));
  }
  function start(){
    const nav=document.getElementById('nav');
    if(nav){
      const label=document.createElement('label');label.className='language-control';
      const select=document.createElement('select');select.id='language-switch';select.setAttribute('aria-label','Language / 语言');
      for(const [value,text] of [['zh-CN','简体中文'],['en','English']]){
        const option=document.createElement('option');option.value=value;option.textContent=text;select.append(option);
      }
      select.value=language;select.addEventListener('change',()=>setLanguage(select.value));label.append(select);nav.append(label);
    }
    apply();new MutationObserver(schedule).observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','placeholder','aria-label']});
  }
  root.BoardI18n=Object.freeze({translate,setLanguage,get language(){return language;}});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window==='object'?window:globalThis);
