import os
def read_system_users():
    return os.popen('cat /etc/passwd').read()
