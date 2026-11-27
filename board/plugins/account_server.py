"""Opt-in accounts on the same direct loopback boundary as the single-user app."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
import base64
import ipaddress
from .. import app,project,storage
from . import accounts,account_roles

LOGIN='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Sign in</title><style>body{font:18px system-ui;max-width:34rem;margin:12vh auto;padding:24px}input,button{font:inherit;padding:12px;margin:8px 0}label{display:block}</style><h1>Research board</h1><form><label>Account password <input type="password" autocomplete="current-password" required></label><button>Sign in</button><p role="status"></p></form><script>document.querySelector('form').onsubmit=async e=>{e.preventDefault();const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:document.querySelector('input').value})});if(r.ok)location.href='/';else document.querySelector('[role=status]').textContent='Please check your password and try again.'}</script></html>'''
GUEST='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Visitor board</title><style>body{font:17px system-ui;max-width:52rem;margin:4vh auto;padding:24px}textarea{box-sizing:border-box;width:100%;height:8rem}button{font:inherit;padding:10px}article{border-bottom:1px solid #aaa;padding:14px 0}p{overflow-wrap:anywhere;white-space:pre-wrap}</style><h1>Visitor board</h1><h2>Discussion</h2><section id="discussion"></section><button id="logout">Sign out</button><script>async function post(path,data){return fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)})}fetch('/api/discussion').then(r=>r.json()).then(v=>{for(const x of v.items){const a=document.createElement('article'),h=document.createElement('strong'),p=document.createElement('p');h.textContent=x.author;p.textContent=x.body;a.append(h,p);document.querySelector('#discussion').append(a)}});document.querySelector('#logout').onclick=async()=>{await post('/api/logout',{});location.reload()}</script></html>'''


def guest_board(root):
    value=storage.read(Path(root)/'overview.json',{})
    return dict(overview=dict(schedule=[{k:day[k] for k in ('date','label') if k in day} | dict(items=[{k:item[k] for k in ('time','what','kind','completed') if k in item} for item in day.get('items',[])]) for day in value.get('schedule',[])]))


def create_server(root,port=8780):
    root=Path(root).resolve();store=accounts.Store(root/'attachments/accounts.json');store.read()
    server=app.create_server(root,port);base=server.RequestHandlerClass;limiter=accounts.LoginLimiter()
    class Handler(base):
        def dispatch(self):
            authority=self.headers.get('Host','')
            if urlsplit('http://'+authority).hostname not in {'localhost','127.0.0.1','::1'} or not ipaddress.ip_address(self.client_address[0]).is_loopback or self.headers.get('Forwarded') or any(k.lower().startswith('x-forwarded-') for k in self.headers):return self.reject('Use the direct local board address')
            if self.command=='POST' and self.headers.get('Origin')!='http://'+authority:return self.reject('Use the board page')
            route=unquote(urlsplit(self.path).path);cfg=store.read()
            if route=='/api/login' and self.command=='POST':
                body=self.body();matches=[]
                def verify():
                    matches.extend(accounts.matching_accounts(cfg,body.get('password')))
                    return len(matches)==1
                status=limiter.attempt(self.client_address[0],verify)
                if status!=303:return self.respond(status,dict(error='A valid account password is required'))
                token=accounts.issue(cfg,matches[0])
                # This listener accepts direct loopback HTTP only; SameSite and Origin bind writes.
                return self.respond(200,dict(signed_in=True),headers=[('Set-Cookie',accounts.cookie(token).replace('; Secure',''))])
            subject=accounts.session(cfg,accounts.cookie_token(self.headers.get('Cookie')))
            if subject is None:
                if route=='/' and self.command in {'GET','HEAD'}:return self.respond(200,LOGIN,'text/html; charset=utf-8')
                return self.respond(401,dict(error='Sign in to the board'))
            uid=subject['sub'];role=account_roles.role(cfg,uid)
            if route=='/api/logout' and self.command=='POST':
                self.body()
                def revoke(value):value['accounts'][uid]['session_version']+=1
                store.update(revoke)
                return self.respond(200,dict(signed_out=True),headers=[('Set-Cookie',f'{accounts.COOKIE}=; Max-Age=0; Path=/; HttpOnly; SameSite=Strict')])
            if route=='/api/me' and self.command in {'GET','HEAD'}:return self.respond(200,dict(id=uid,display_name=cfg['accounts'][uid]['display_name'],role=role))
            if role=='owner':return super().dispatch()
            if not account_roles.allowed(role,self.command,route):return self.reject('This action belongs to the project owner')
            if route=='/':return self.respond(200,GUEST,'text/html; charset=utf-8')
            if route=='/api/board':return self.respond(200,guest_board(root))
            if route=='/api/avatar':
                from . import asset_choices
                directory=root/'attachments/avatar-catalog';state=root/'attachments/avatar-choices'
                if self.command=='POST':
                    body=self.body()
                    if set(body)!={'id','crop'}:raise ValueError('Choose a catalog image and square crop')
                    return self.respond(200,asset_choices.select(directory,state,uid,body['id'],body['crop']))
                result=dict(choices=asset_choices.catalog(directory) if (directory/'catalog.json').is_file() else [],selection=asset_choices.current(state).get(uid))
                if result['selection']:
                    path=asset_choices.contained(state,result['selection']['file']);result['image']='data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
                return self.respond(200,result)
            if route=='/api/discussion':
                items=[{k:row.get(k) for k in ('author','body','created_at')} for row in project.all_posts(root) if row.get('channel','main')=='main' and not row.get('deleted')]
                return self.respond(200,dict(items=items))
            return self.respond(404,dict(error='Choose a visitor action'))
    server.RequestHandlerClass=Handler
    return server
