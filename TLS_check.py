import ssl, socket
from whoisInfo import grab_domain

def tls_cert(url: str):
    domain = grab_domain(url)
    context = ssl.create_default_context()
    address = (domain, 443)
    try:
        with socket.create_connection(address) as sock:
            with context.wrap_socket(sock, server_hostname=address[0]) as wsock:
                print(wsock.getpeercert())
                return wsock.getpeercert() # dict
    except ssl.SSLError:
        print("Invalid certificate.")
    except Exception:
        print("Connection error.")
        
# Just for testing
tls_cert("https://www.nvidia.com/zh-tw/")