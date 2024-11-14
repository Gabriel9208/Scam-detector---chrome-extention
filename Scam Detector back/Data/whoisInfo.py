import socket
import whois
from urllib.parse import urlparse
import logging
import time
import signal

def urlToDomain(url: str) -> str:
    subDomain = urlparse(url).netloc
    rawWhois = whois.whois(subDomain).text
    domainName = None

    for line in rawWhois.splitlines():
        if "Domain Name" in line:
            domainName = line.split(":", 1)[1].strip()
            break

    return domainName

def getAuthoritativeWhoisServer(domain: str) -> tuple[str, str, str]:
    """
    Gets the authoritative WHOIS server, domain name, and raw WHOIS data for a domain.

    Args:
        domain (str): The domain name to query

    Returns:
        tuple[str, str, str]: A tuple containing:
            - registrarWhoisServer: The authoritative WHOIS server for the domain
            - domainName: The domain name extracted from WHOIS data
            - rawWhois: The complete raw WHOIS response
    """
    rawWhois = whois.whois(domain).text
    time.sleep(1)
    registrarWhoisServer = None
    domainName = None

    for line in rawWhois.splitlines():
        if "Registrar WHOIS Server" in line:
            registrarWhoisServer = line.split(":", 1)[1].strip()
            logging.info(f"Registrar WHOIS Server: {registrarWhoisServer}")
        if "Domain Name" in line:
            domainName = line.split(":", 1)[1].strip()
        if registrarWhoisServer and domainName:
            break
    
    logging.info(f"WHOIS data: {rawWhois}")

    return registrarWhoisServer, domainName, rawWhois

def queryWhoisServer(registrarWhois: str, queryDomain: str) -> str:
    """
    Query a WHOIS server for domain information.

    Args:
        registrarWhois (str): The WHOIS server hostname to query
        queryDomain (str): The domain name to look up

    Returns:
        str: The WHOIS response text, cleaned of any trailing data after '>'

    Raises:
        SystemExit: If the TCP connection fails
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

    logging.info(f"WHOIS data: {response.decode()}")

    cleanedResponse = response.decode().split(">", 1)[0]
    return cleanedResponse
            
def toJson(whoisData: str) -> dict:
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
    Search WHOIS information for a given URL.
    
    Args:
        url (str): The URL to search WHOIS information for
        
    Returns:
        dict: A dictionary containing the parsed WHOIS information with fields like:
            - Domain Name
            - Creation Date 
            - Expiration Date
            - Registrar
            - etc.
            
    The function first extracts the domain from the URL, then queries the authoritative 
    WHOIS server if available, otherwise uses the raw WHOIS data. The WHOIS data is 
    then parsed into a structured dictionary format.
    """
    domain = urlparse(url).netloc 
    
    whoisServer, domainName, rawWhois = getAuthoritativeWhoisServer(domain) 
    whoisData = None
    
    if whoisServer:
        try:
            logging.info(f"Querying WHOIS server: {whoisServer}")
            whoisData = queryWhoisServer(whoisServer, domainName)
            
            if whoisData == {}:
                whoisData = rawWhois
        except Exception as e:
            logging.info(f"Error querying WHOIS server: {e}")
            whoisData = rawWhois
    else:
        whoisData = rawWhois
    

    whoisJson = toJson(whoisData)
    
    logging.info(f"WHOIS data: {whoisJson}")
    return whoisJson

if __name__ == "__main__":
    print(searchWhois("https://tw.yahoo.com/"))
