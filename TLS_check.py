import ssl, socket
from urllib.parse import urlparse
def fetch_tls_cert(url: str) -> dict:
    """
    Fetches the TLS certificate for a given URL.

    Args:
        url (str): The URL to fetch the TLS certificate for.

    Returns:
        dict: The TLS certificate as a dictionary.

    Raises:
        ssl.SSLError: If the certificate is invalid.
        Exception: If there is an error connecting to the server.
    """
    domain = urlparse(url).netloc
    context = ssl.create_default_context()
    address = (domain, 443)

    try:
        with socket.create_connection(address) as sock:
            with context.wrap_socket(sock, server_hostname=address[0]) as wsock:
                
                return wsock.getpeercert() # dict
    except ssl.SSLError:
        raise ssl.SSLError("Invalid certificate.")
    except Exception:
        raise Exception("Connection error.")
        
# Just for testing
# fetch_tls_cert("https://www.nvidia.com/zh-tw/")