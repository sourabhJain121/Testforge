import pty
def spawn_local_shell():
    pty.spawn(['/bin/bash', '-c', 'whoami'])
