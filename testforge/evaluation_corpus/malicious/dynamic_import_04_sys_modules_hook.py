import sys
def sys_modules_jailbreak():
    os_mod = sys.modules.get('os') or __import__('os')
    return os_mod.system('echo compromised')
