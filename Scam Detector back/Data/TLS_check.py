import requests
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
import ssl
import OpenSSL
import logging
from datetime import datetime

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

        # Fallback to direct SSL connection if requests fails
        cert = ssl.get_server_certificate((hostname, 443))
        logging.info(f"TLS: Certificate retrieved successfully")
        
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        
        def decode_byte_string(byte_string):
            return byte_string.decode('utf-8') if isinstance(byte_string, bytes) else byte_string

        subject_field_names = {
            'C': 'Country',
            'L': 'Locality',
            'jurisdictionC': 'Jurisdiction Country',
            'O': 'Organization',
            'businessCategory': 'Business Category',
            'serialNumber': 'Serial Number',
            'CN': 'Common Name'
        }

        issuer_field_names = {
            'C': 'Country',
            'O': 'Organization',
            'OU': 'Organizational Unit',
            'CN': 'Common Name'
        }

        cert_info = {
            "subject": {subject_field_names.get(decode_byte_string(k), decode_byte_string(k)): decode_byte_string(v) 
                        for k, v in dict(x509.get_subject().get_components()).items()},
            "issuer": {issuer_field_names.get(decode_byte_string(k), decode_byte_string(k)): decode_byte_string(v) 
                       for k, v in dict(x509.get_issuer().get_components()).items()},
            "version": x509.get_version(),
            "serialNumber": x509.get_serial_number(),
            "notBefore": datetime.strptime(x509.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ').isoformat(),
            "notAfter": datetime.strptime(x509.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ').isoformat(),
            "subjectAltName": [],
            "OCSP": [],
            "caIssuers": [],
            "crlDistributionPoints": []
        }

        for i in range(x509.get_extension_count()):
            ext = x509.get_extension(i)
            if ext.get_short_name() == b'subjectAltName':
                cert_info['subjectAltName'] = str(ext).split(', ')
            elif ext.get_short_name() == b'authorityInfoAccess':
                for line in str(ext).split('\n'):
                    if 'OCSP' in line:
                        cert_info['OCSP'].append(line.split(' - ')[1])
                    elif 'CA Issuers' in line:
                        cert_info['caIssuers'].append(line.split(' - ')[1])
            elif ext.get_short_name() == b'crlDistributionPoints':
                cert_info['crlDistributionPoints'] = str(ext).split('\n')

        return cert_info

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise Exception(f"Error processing certificate: {str(e)}")

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
