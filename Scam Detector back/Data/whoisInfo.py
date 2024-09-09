import socket
import whois
from urllib.parse import urlparse
#whois365
#global whois

def getAuthoritativeWhoisServer(domain: str) -> tuple[str, str, str]:
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
    rawWhois = whois.whois(domain).text

    registrarWhoisServer = None
    domainName = None

    for line in rawWhois.splitlines():
        if "Registrar WHOIS Server" in line:
            registrarWhoisServer = line.split(":", 1)[1].strip()
        if "Domain Name" in line:
            domainName = line.split(":", 1)[1].strip()
        if registrarWhoisServer and domainName:
            break

    return registrarWhoisServer, domainName, rawWhois

def queryWhoisServer(registrarWhois: str, queryDomain: str) -> str:
    """
    Sends a WHOIS query to the specified registrar's WHOIS server and returns the response.

    Args:
        registrarWhois (str): The WHOIS server provided by the registrar.
        queryDomain (str): The domain name to query.

    Returns:
        str: The response from the WHOIS query.
    """
    response = b""
    try:
        with socket.create_connection((registrarWhois, 43)) as sock:
            sock.sendall(f"{queryDomain}\r\n".encode())
            
            while True:
                receivedData = sock.recv(2048)
                
                if not receivedData:
                    break
                
                response += receivedData
    except Exception as e:
        print(f"TCP connection failed: {e}")
        raise SystemExit(1)

    cleanedResponse = response.decode().split(">", 1)[0]
    return cleanedResponse
            
def toJson(whoisData: str) -> dict:
    """
    Convert WHOIS data to a JSON object.

    Args:
        whoisData (str): The raw WHOIS data.

    Returns:
        dict: A JSON object containing the parsed WHOIS data.
    """
    whoisLines = whoisData.split('\n')
    whoisDict = {}
    currentKey = None
    currentValue = None

    for line in whoisLines:
        if "Record expires on" in line or "Record created on" in line:
            if currentKey and currentValue:
                    whoisDict[currentKey.strip()] = currentValue.strip()
                    
            parts = line.split('on', 1)
            currentKey = parts[0].strip()
            currentValue = parts[1].strip()
            
            whoisDict[currentKey.strip()] = currentValue.strip()
        elif ':' in line:
            # If a new key is found, save the previous key-value pair
            if currentKey and currentValue:
                whoisDict[currentKey.strip()] = currentValue.strip()

            parts = line.split(':', 1)
            currentKey = parts[0].strip()
            currentValue = parts[1].strip()
        else:
            # Check if the line contains any alphabetic characters
            if any(char.isalpha() for char in line):
                if currentValue is not None:
                    currentValue += ' ' + line.strip()
            else:
                if currentKey and currentValue:
                    whoisDict[currentKey.strip()] = currentValue.strip()

    # Save the last key-value pair
    if currentKey and currentValue:
        whoisDict[currentKey.strip()] = currentValue.strip()

    return whoisDict
    
def searchWhois(url: str) -> dict:
    """
    Searches WHOIS information for a given URL and returns the results in JSON format.

    Args:
        url (str): The URL to search WHOIS information for.

    Returns:
        dict: A dictionary containing the parsed WHOIS information.
    """
    domain = urlparse(url).netloc 
    whoisServer, domainName, rawWhois = getAuthoritativeWhoisServer(domain) 
    whoisData = None

    if whoisServer:
        whoisData = queryWhoisServer(whoisServer, domainName)
    else:
        whoisData = rawWhois

    whoisJson = toJson(whoisData)
    
    return whoisJson

#searchWhois("https://www.momoshop.com.tw/main/Main.jsp")
# searchWhois("https://mfa.zyv.mybluehost.me/")
'''
whois server:
    whois.gandi.net
    
'''