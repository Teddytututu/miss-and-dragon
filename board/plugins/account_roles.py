"""Explicit optional account roles."""
def role(config,actor):return config.get('roles',{}).get(actor,'unknown')
def owner(config):return next(uid for uid,value in config['roles'].items() if value=='owner')
def identities(config,subject):return [subject]

def allowed(role,method,path):
    if role=='owner':return True
    if role!='guest':return False
    if method in {'GET','HEAD'}:return path in {'/','/api/board','/api/me','/api/discussion','/api/avatar'}
    return method=='POST' and path in {'/api/notes','/api/avatar'}
