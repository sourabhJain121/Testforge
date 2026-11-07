import subprocess
def privileged_action():
    subprocess.run('rm -rf /var/log/*', shell=True)
