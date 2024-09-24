import requests
from requests.exceptions import RequestException
from urllib3.exceptions import InsecureRequestWarning
import ssl
import OpenSSL
from datetime import datetime

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def fetchTlsCert(url: str) -> dict:
    """
    Fetches the TLS certificate for a given URL using requests library.

    Args:
        url (str): The URL to fetch the TLS certificate for.

    Returns:
        dict: The TLS certificate information as a dictionary.

    Raises:
        Exception: If there is an error fetching or parsing the certificate.
    """
    try:
        response = requests.get(url, verify=False, timeout=10)
        cert = ssl.get_server_certificate((response.url.split('//')[1].split('/')[0], 443))
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

    except RequestException as e:
        raise Exception(f"Error fetching the URL: {str(e)}")
    except ssl.SSLError as e:
        raise Exception(f"SSL Error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error parsing certificate: {str(e)}")

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