import os
def execute_ping(ip: str):
    os.system(f'ping -c 1 {ip}')
