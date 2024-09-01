import socket
from whois import whois
from urllib.parse import urlparse
from pprint import pprint
#whois365
#global whois

def get_authoritative_whois_server(domain: str) -> tuple[str, str, str]:
    """
    Retrieves the authoritative whois server for a given domain.

    Args:
        domain (str): The domain name to query.

    Returns:
        tuple: A tuple containing the whois server provided by the registrar,
            the domain name itself, and the raw text output from the WHOIS query.

    Raises:
        ValueError: If the registrar WHOIS server is not found.
    """
    raw_whois = whois(domain).text

    registrar_whois_server = None
    domain_name = None

    for line in raw_whois.splitlines():
        if "Registrar WHOIS Server" in line:
            registrar_whois_server = line.split(":", 1)[1].strip()
        if "Domain Name" in line:
            domain_name = line.split(":", 1)[1].strip()
        if registrar_whois_server and domain_name:
            break

    pprint(raw_whois)

    return registrar_whois_server, domain_name, raw_whois

def query_whois_server(registrar_whois: str, query_domain: str) -> str:
    """
    Sends a WHOIS query to the specified registrar's WHOIS server and returns the response.

    Args:
        registrar_whois (str): The WHOIS server provided by the registrar.
        query_domain (str): The domain name to query.

    Returns:
        str: The response from the WHOIS query.
    """
    response = b""
    try:
        with socket.create_connection((registrar_whois, 43)) as sock:
            sock.sendall(f"{query_domain}\r\n".encode())
            
            while True:
                received_data = sock.recv(2048)
                
                if not received_data:
                    break
                
                response += received_data
    except Exception as e:
        print(f"TCP connection failed: {e}")
        raise SystemExit(1)

    cleaned_response = response.decode().split(">", 1)[0]
    return cleaned_response
            
def to_json(whois_data: str) -> dict:
    """
    Convert WHOIS data to a JSON object.

    Args:
        whois_data (str): The raw WHOIS data.

    Returns:
        dict: A JSON object containing the parsed WHOIS data.
    """
    whois_lines = whois_data.split('\n')
    whois_dict = {}
    current_key = None
    current_value = None

    for line in whois_lines:
        if "Record expires on" in line or "Record created on" in line:
            if current_key and current_value:
                    whois_dict[current_key.strip()] = current_value.strip()
                    
            parts = line.split('on', 1)
            current_key = parts[0].strip()
            current_value = parts[1].strip()
            
            whois_dict[current_key.strip()] = current_value.strip()
        elif ':' in line:
            # If a new key is found, save the previous key-value pair
            if current_key and current_value:
                whois_dict[current_key.strip()] = current_value.strip()

            parts = line.split(':', 1)
            current_key = parts[0].strip()
            current_value = parts[1].strip()
        else:
            # Check if the line contains any alphabetic characters
            if any(char.isalpha() for char in line):
                if current_value is not None:
                    current_value += ' ' + line.strip()
            else:
                if current_key and current_value:
                    whois_dict[current_key.strip()] = current_value.strip()

    # Save the last key-value pair
    if current_key and current_value:
        whois_dict[current_key.strip()] = current_value.strip()

    return whois_dict
    
def search_whois(url: str) -> dict:
    """
    Searches WHOIS information for a given URL and returns the results in JSON format.

    Args:
        url (str): The URL to search WHOIS information for.

    Returns:
        dict: A dictionary containing the parsed WHOIS information.
    """
    domain = urlparse(url).netloc 
    whois_server, domain_name, raw_whois = get_authoritative_whois_server(domain) 
    whois_data = None

    if whois_server:
        whois_data = query_whois_server(whois_server, domain_name)
    else:
        whois_data = raw_whois

    whois_json = to_json(whois_data)
    
    pprint(whois_json)
    return whois_json

#search_whois("https://www.momoshop.com.tw/main/Main.jsp")
# search_whois("https://mfa.zyv.mybluehost.me/")
'''
whois server:
    whois.gandi.net
    
'''