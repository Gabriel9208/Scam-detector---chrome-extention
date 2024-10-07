import requests
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import logging
import socket

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def fetchTlsCert(url: str) -> dict:
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

    try:
        logging.info(f"TLS: Fetching TLS certificate for URL: {url}")
        
        # Try with requests first
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()
            logging.info(f"TLS: Response status code: {response.status_code}")
            hostname = response.url.split('//')[1].split('/')[0]
        except RequestException as req_err:
            logging.warning(f"Request failed, falling back to direct SSL: {req_err}")
            hostname = url.split('//')[1].split('/')[0]

        # Use ssl.create_default_context() instead of get_server_certificate
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as secure_sock:
                der_cert = secure_sock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(der_cert, default_backend())

        logging.info(f"TLS: Certificate retrieved successfully")
        
        # Use the cert object to extract information
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
        logging.error(f"Unexpected error: {str(e)}")
        #raise Exception(f"Error processing certificate: {str(e)}")
        return {}

# For testing
if __name__ == "__main__":
    test_url = "https://www.dbs.com.tw/personal-zh/default.page"
    try:
        cert = fetchTlsCert(test_url)
        print(f"Certificate details for {test_url}:")
        for key, value in cert.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error: {str(e)}")
