import ipaddress

def is_private_network_ip(ip_str: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip_str.strip())
        return addr.is_private or addr.is_loopback
    except ValueError:
        return False
