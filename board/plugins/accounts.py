"""Account storage and versioned, signed sessions. Importing performs no I/O."""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from http.cookies import SimpleCookie, CookieError
from pathlib import Path

LOCK = threading.RLock()
RESERVED = {'claude', 'gpt'}
COOKIE = 'board_session'
LIFETIME = 400 * 86400
RENEW_BELOW = 300 * 86400
ITERATIONS = 300000


class Rejected(ValueError):
    def __init__(self, message='请求需要有效身份。', status=403):
        super().__init__(message)
        self.status = status


def human_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,31}', value) or value.casefold() in RESERVED:
        raise Rejected('请选择人类账户。')
    return value


def password_hash(password):
    if not isinstance(password, str) or not 10 <= len(password) <= 1024:
        raise Rejected('请使用 10 至 1024 位口令。', 400)
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${digest.hex()}'


def valid_hash(encoded):
    if not isinstance(encoded, str):
        return False
    match = re.fullmatch(r'pbkdf2_sha256\$(\d{5,7})\$([a-f0-9]{32,128})\$([a-f0-9]{64})', encoded)
    return bool(match and 100000 <= int(match[1]) <= 2000000 and len(match[2]) % 2 == 0)


def verify_password(encoded, password):
    if not valid_hash(encoded) or not isinstance(password, str) or len(password) > 1024:
        return False
    _, count, salt, digest = encoded.split('$')
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(count)).hex()
    return hmac.compare_digest(actual, digest)


def initial_config(people=None,roles=None):
    people={'owner':'Project owner','visitor':'Visitor'} if people is None else people
    roles={'owner':'owner','visitor':'guest'} if roles is None else roles
    return validate(dict(schema=1,secret=secrets.token_hex(32),roles=roles,
        accounts={uid:dict(id=uid,display_name=name,password_hash='',session_version=0,avatar=None) for uid,name in people.items()}))


def validate(cfg):
    if cfg.get('schema') != 1 or not re.fullmatch(r'[a-f0-9]{64}', cfg.get('secret', '')):
        raise Rejected('账户配置需要初始化。', 503)
    people = cfg.get('accounts')
    if not isinstance(people, dict) or not people:
        raise Rejected('账户配置需要初始化。', 503)
    if 'roles' in cfg:
        roles=cfg['roles']
        if not isinstance(roles,dict) or set(roles)!=set(people) or any(r not in {'owner','guest'} for r in roles.values()) or list(roles.values()).count('owner')!=1:
            raise Rejected('账户角色需要指定一位所有者及访客。',503)
    else:raise Rejected('Explicit account roles required',503)
    for uid, row in people.items():
        human_id(uid)
        if row.get('id') != uid or not isinstance(row.get('display_name'), str) or not 1 <= len(row['display_name']) <= 40:
            raise Rejected('账户资料需要修复。', 503)
        if row['display_name'].strip().casefold() in RESERVED or row['display_name'].strip() in {'Claude', 'GPT'}:
            raise Rejected('显示名属于保留身份。', 400)
        if not isinstance(row.get('session_version'), int) or row['session_version'] < 0:
            raise Rejected('账户资料需要修复。', 503)
        if row.get('password_hash') and not valid_hash(row['password_hash']):
            raise Rejected('账户哈希需要修复。', 503)
    return cfg


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + secrets.token_hex(8) + '.tmp')
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, path):
        self.path = Path(path)

    def read(self):
        try:
            return validate(json.loads(self.path.read_text(encoding='utf-8-sig')))
        except (OSError, ValueError, TypeError, AttributeError, KeyError):
            raise Rejected('账户配置需要初始化。', 503) from None

    def update(self, change):
        with LOCK:
            cfg = self.read()
            change(cfg)
            atomic_json(self.path, validate(cfg))

    def add_account(self, uid, display_name):
        human_id(uid)
        def change(cfg):
            if uid in cfg['accounts']:
                raise Rejected('账户已存在。', 409)
            cfg['accounts'][uid] = dict(id=uid, display_name=display_name, password_hash='', session_version=0, avatar=None)
        self.update(change)

    def set_password(self, uid, password):
        human_id(uid)
        encoded = password_hash(password)
        def change(cfg):
            if uid not in cfg['accounts']:
                raise Rejected('请选择已有账户。', 404)
            matches = [other for other, row in cfg['accounts'].items()
                       if other != uid and verify_password(row.get('password_hash'), password)]
            if matches:
                raise Rejected('请为各账户使用单独的口令。', 409)
            cfg['accounts'][uid]['password_hash'] = encoded
            cfg['accounts'][uid]['session_version'] += 1
        self.update(change)

    def rotate_secret(self):
        self.update(lambda cfg: cfg.update(secret=secrets.token_hex(32)))


def credential_version(row):
    return hashlib.sha256((str(row['session_version']) + ':' + row.get('password_hash', '')).encode()).hexdigest()


def issue(cfg, uid, now=None):
    now = int(time.time() if now is None else now)
    row = cfg['accounts'][human_id(uid)]
    if not row.get('password_hash'):
        raise Rejected('请先为账户设置口令。', 401)
    payload = dict(sub=uid, iat=now, exp=now + LIFETIME, ver=credential_version(row))
    encoded = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).rstrip(b'=').decode()
    signature = hmac.new(cfg['secret'].encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return encoded + '.' + signature


def session(cfg, token, now=None):
    now = int(time.time() if now is None else now)
    try:
        if len(token) > 2048:
            return None
        encoded, signature = token.split('.')
        expected = hmac.new(cfg['secret'].encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(base64.b64decode(encoded + '=' * (-len(encoded) % 4), altchars=b'-_', validate=True))
        uid = human_id(payload['sub'])
        row = cfg['accounts'][uid]
        if (type(payload['exp']) is not int or type(payload['iat']) is not int or
                not payload['iat'] <= now < payload['exp'] or payload['exp'] - payload['iat'] != LIFETIME or
                not row.get('password_hash') or payload['ver'] != credential_version(row)):
            return None
        return payload
    except (ValueError, KeyError, TypeError, UnicodeError, Rejected):
        return None


def cookie_token(header):
    if len(header or '') > 8192:
        return ''
    try:
        jar = SimpleCookie()
        jar.load(header or '')
        return jar[COOKIE].value if COOKIE in jar else ''
    except CookieError:
        return ''


def cookie(token):
    return f'{COOKIE}={token}; Max-Age={LIFETIME}; Path=/; HttpOnly; Secure; SameSite=Strict'


class LoginLimiter:
    """Five failures trigger a full 15-minute cooldown, keyed by trusted transport."""
    def __init__(self):
        self.attempts = {}
        self.lock = threading.Lock()

    def attempt(self, peer, verify, now=None):
        now = time.time() if now is None else now
        with self.lock:
            self.attempts = {key: val for key, val in self.attempts.items() if now < val[1]}
            count, until = self.attempts.get(peer, (0, now + 900))
            if count >= 5:
                return 429
            if verify():
                self.attempts.pop(peer, None)
                return 303
            self.attempts[peer] = (count + 1, now + 900 if count + 1 >= 5 else until)
            return 401


def matching_accounts(cfg, password):
    """Evaluate every hash before deciding; usernames never select the subject."""
    results = [(uid, verify_password(row.get('password_hash'), password))
               for uid, row in cfg['accounts'].items()]
    return [uid for uid, matched in results if matched]
