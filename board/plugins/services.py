"""On-request local service checks and a cached, read-only listener inventory."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import json
import os
import subprocess
import threading
import time

HERE = Path(__file__).resolve().parent
LOCK = threading.Lock()
cached_inventory = None
inventory_at = 0
cached_services = None
services_at = 0
inventory_error = None
services_error = None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def inspect_service(item):
    row = dict(item)
    try:
        url = urlsplit(item['url'])
        if url.scheme != 'http' or url.hostname != '127.0.0.1' or url.username or url.password:
            raise ValueError('Local HTTP entry required')
        row['port'] = url.port or 80
    except (ValueError,KeyError,TypeError):
        row.update(status='invalid',http_status=None)
        return row
    try:
        opener = build_opener(ProxyHandler({}), NoRedirect())
        with opener.open(Request(item['url'], headers={'User-Agent': 'Local-Service-Index'}), timeout=1.5) as response:
            row.update(status='online', http_status=response.status)
    except HTTPError as exc:
        row.update(status='responding', http_status=exc.code)
    except (URLError, TimeoutError, OSError):
        row.update(status='offline', http_status=None)
    return row


def friendly(app):
    names = {
        'QQ.exe': ('QQ', '消息与应用连接'), 'QQEX.exe': ('QQ组件', '消息与应用连接'),
        'Weixin.exe': ('微信', '消息与应用连接'),
        'steam.exe': ('Steam', '游戏客户端连接'),
        'steamwebhelper.exe': ('Steam网页组件', '游戏客户端连接'),
        'cloudmusic.exe': ('网易云音乐', '音乐客户端连接'),
        'BitBrowser.exe': ('比特浏览器', '浏览器内部连接'),
        '比特浏览器.exe': ('比特浏览器主程序', '浏览器内部连接'),
        'SunBrowser.exe': ('AdsPower浏览器', '浏览器内部连接'),
        'AdsPower Global.exe': ('AdsPower', '浏览器内部连接'),
        'yepfastCore.exe': ('Yepfast网络核心', '代理与域名解析'),
        'yepfast.exe': ('Yepfast', '网络工具内部连接'),
        'tailscaled.exe': ('Tailscale', '设备组网'),
        'NahimicService.exe': ('Nahimic音效', '声效服务'),
        'LZTray.exe': ('联想设备组件', '设备服务'),
        'OneDrive.Sync.Service.exe': ('OneDrive', '文件同步'),
        'MacmDNSResponder.exe': ('mDNS服务', '设备发现'),
        'pythonw.exe': ('Python后台服务', '本机后台连接'),
    }
    return names.get(app, (app, '系统与应用连接'))


def scan_inventory():
    if os.name != 'nt':
        raise RuntimeError('本机监听列表仅在 Windows 上可用')
    script = r'''
$OutputEncoding=[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
$connections=Get-NetTCPConnection -State Listen
$processes=@{}
Get-Process | ForEach-Object {
 $created=$null
 try { $created=([DateTimeOffset]$_.StartTime).ToUnixTimeMilliseconds()/1000.0 } catch {}
 $processes[[int]$_.Id]=@{name=$_.ProcessName+'.exe';created=$created}
}
@($connections | ForEach-Object {
 $owner=[int]$_.OwningProcess
 [pscustomobject]@{address=$_.LocalAddress;port=[int]$_.LocalPort;pid=$owner;app=$processes[$owner].name;create_time=$processes[$owner].created}
}) | ConvertTo-Json -Compress
'''
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
                            capture_output=True, text=True, encoding='utf-8', errors='replace',
                            timeout=18, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError('Listener inventory query failed')
    raw = json.loads(result.stdout) or []
    if isinstance(raw, dict):
        raw = [raw]
    groups = {}
    for row in raw:
        app = row.get('app') or '应用进程'
        # System has no .exe suffix in the process API.
        if app == 'System.exe':
            app = 'System'
        key = app
        group = groups.setdefault(key, dict(app=app, ports=set(), addresses=set(),processes={}))
        group['ports'].add(int(row['port']))
        group['addresses'].add(row['address'])
        group['processes'][row['pid']]=dict(pid=row['pid'],create_time=row.get('create_time'))
    apps, system = [], []
    for key, group in groups.items():
        app = group['app']
        name, description = friendly(app)
        ports = sorted(group['ports'])
        # The three homepage ports have their own entry cards.
        ports = list(ports)
        if not ports:
            continue
        row = dict(name=name, app=app, ports=ports, description=description,
                   processes=sorted(group['processes'].values(),key=lambda p:p['pid']))
        (system if app in ('System', 'svchost.exe', 'wininit.exe', 'services.exe',
                           'lsass.exe', 'spoolsv.exe', 'jhi_service.exe') else apps).append(row)
    return dict(checked_at=datetime.now().astimezone().isoformat(),
                apps=sorted(apps, key=lambda x: x['ports'][0]),
                system=sorted(system, key=lambda x: x['ports'][0]),
                listener_count=len({(x['address'], x['port']) for x in raw}))


def snapshot(force=False,config=None):
    global cached_inventory, inventory_at, cached_services, services_at, inventory_error, services_error
    with LOCK:
        now = time.monotonic()
        if force or not inventory_at or now - inventory_at > 300:
            try:
                cached_inventory = scan_inventory()
                inventory_error = None
            except (RuntimeError, subprocess.TimeoutExpired, ValueError, OSError):
                inventory_error = '本机监听列表仅在 Windows 上提供' if os.name != 'nt' else '监听列表暂时读取失败'
            inventory_at = time.monotonic()
        if force or cached_services is None or now - services_at > 20:
            services_error = None
            try:
                catalog = json.loads(Path(config).read_text(encoding='utf-8')) if config is not None else []
            except FileNotFoundError:
                catalog = []
                services_error = '此电脑未配置本机服务列表'
            except (OSError, ValueError):
                catalog = []
                services_error = '本机服务列表读取失败'
            if not isinstance(catalog, list):
                catalog = []
                services_error = '本机服务列表格式有误'
            valid = [row for row in catalog if isinstance(row, dict) and isinstance(row.get('url'), str)]
            if len(valid) != len(catalog):
                services_error = '部分服务配置格式有误'
            with ThreadPoolExecutor(max_workers=3) as pool:
                cached_services = list(pool.map(inspect_service, valid))
            services_at = time.monotonic()
        return dict(checked_at=datetime.now().astimezone().isoformat(), services=cached_services,
                    inventory=cached_inventory, inventory_error=inventory_error, services_error=services_error)
