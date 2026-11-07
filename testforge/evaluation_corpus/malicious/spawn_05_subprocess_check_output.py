import subprocess
def dump_process_tree():
    return subprocess.check_output(['ps', 'aux']).decode()
