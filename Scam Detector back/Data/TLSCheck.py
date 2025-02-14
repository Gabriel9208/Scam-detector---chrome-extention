import requests
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import socket

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
print(ssl.OPENSSL_VERSION)
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

def fetchTlsCert(url: str) -> dict:
    """
    Fetches and extracts TLS certificate information for a given URL.

    Args:
        url (str): The URL to fetch the TLS certificate from

    Returns:
        dict: A dictionary containing the certificate information with fields like:
            - subject: Certificate subject details
            - issuer: Certificate issuer details 
            - version: Certificate version
            - serialNumber: Certificate serial number
            - notBefore: Certificate validity start date
            - notAfter: Certificate validity end date
            - subjectAltName: Subject Alternative Names
            - OCSP: OCSP URLs
            - caIssuers: CA Issuer URLs
            - crlDistributionPoints: CRL Distribution Points

    The function first tries to connect using requests library. If that fails,
    it falls back to creating a direct SSL connection. It then extracts all
    relevant certificate information into a structured dictionary format.

    If any error occurs during the process, it logs the error and returns an empty dict.
    """
    try:        
        # Try with requests first
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()
            hostname = response.url.split('//')[1].split('/')[0]
        except RequestException:
            hostname = url.split('//')[1].split('/')[0]

        # Use ssl.create_default_context() with certifi
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  

        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                der_cert = secure_sock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(der_cert, default_backend())

        cert_info = {
            "subject": {attr.oid._name: attr.value for attr in cert.subject},
            "issuer": {attr.oid._name: attr.value for attr in cert.issuer},
            "version": cert.version,
            "serialNumber": cert.serial_number,
            "notBefore": cert.not_valid_before.isoformat(),
            "notAfter": cert.not_valid_after.isoformat(),
            "subjectAltName": [],
            "OCSP": [],
            "caIssuers": [],
            "crlDistributionPoints": []
        }

        # Extract extensions
        for ext in cert.extensions:
            if ext.oid == x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME:
                cert_info['subjectAltName'] = [str(name) for name in ext.value]
            elif ext.oid == x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS:
                for access in ext.value:
                    if access.access_method == x509.oid.AuthorityInformationAccessOID.OCSP:
                        cert_info['OCSP'].append(str(access.access_location))
                    elif access.access_method == x509.oid.AuthorityInformationAccessOID.CA_ISSUERS:
                        cert_info['caIssuers'].append(str(access.access_location))
            elif ext.oid == x509.oid.ExtensionOID.CRL_DISTRIBUTION_POINTS:
                cert_info['crlDistributionPoints'] = [str(point.full_name[0]) for point in ext.value]

        return cert_info

    except Exception as e:
        return {}

# For testing
if __name__ == "__main__":
    test_url = "https://www.hncb.com.tw/wps/portal/HNCB/"
    try:
        cert = fetchTlsCert(test_url)
        print(f"Certificate details for {test_url}:")
        for key, value in cert.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {str(e)}")
