from Data.whoisInfo import searchWhois, urlToDomain
from Data.TLS_check import fetchTlsCert
from Data.findbiz import findbiz
from Data.scraper import scraper
from concurrent.futures import ThreadPoolExecutor, as_completed

def classify(obj) -> str:
    if not obj:
        return 'Not found'

    if 'subject' in obj:
        return 'tls'
    elif 'Domain Name' in obj:
        return 'whois'
    elif "Business_Accounting_NO" in obj: 
        return 'biz'
    else:
        return 'con'

in_url = input("Enter url: ")
result = []

whois = None
tls = None
biz = None
con = None


with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(urlToDomain, in_url), 
               executor.submit(scraper, in_url),
               executor.submit(searchWhois, in_url), 
               executor.submit(fetchTlsCert, in_url),]
    
    bizDomain = None
    
    for future in as_completed(futures):
        if type(future.result()) is dict:
            result.append(future.result())
        else:
            bizDomain = future.result()
        
    bizFuture = executor.submit(findbiz, bizDomain)
    result.append(bizFuture.result())
    
for i in result:
    match classify(i):
        case 'whois': whois = i
        case 'tls': tls = i
        case 'biz': biz = i
        case 'con': con = i
        
print(whois)
print(tls)
print(biz)
print(con)

whoisSection = ""
tlsSection = ""
biz = ""
con = ""

"""
(* 表示重要)
Domain: 
    - creation date (越早越不可疑)
    - *expiration date (過期了沒)
    - *Registrant (是否符合網站內容)
TLS:
    - notBefore
    - notAfter
    - subjectorganizationName
    - CA (Well-known CA or local CA like TWCA. a list is needed)
    - 
    
Compare organization name and domain name in both whois and tls


13 weeks:
9/9-9/16: Backend setup / Backend logic(including simple data analyzing)
9/16-9/23: Backend logic / Frontend layout 
9/23-9/30: Integration and testing -- v1 (summarized information can be shown in browser) 
9/30-10/7: Documentation -- v1
10/7-10/14: Add feature: Implement Content Analysis
10/14-10/21: Add feature: check if the site is already flagged -> Google Safe Browsing API / PhishTank API
10/21-10/28: Add feature: Backlink Analysis (https://www.seoptimer.com/backlink-checker/ + selenium)
10/28-11/4: Integration and testing / Documentation -- v2
11/4-11/11: Prepare for presentation and poster design


{
    "Domain Name": "nccc.com.tw",
    "Domain Status": "ok",
    "Registrant": "財團法人聯合信用卡處理中心 National Credit Card Center brad.wu@nccc.com.tw TW (Redacted for privacy)",
    "Administrative Contact": "(Redacted for privacy)",
    "Technical Contact": "(Redacted for privacy)",
    "Record expires": "2026-05-31 00:00:00 (UTC+8)",
    "Record created": "1984-09-29 00:00:00 (UTC+8)",
    "Domain servers in listed order": "3dns1.nccc.com.tw     210.61.215.247 3dns3.nccc.com.tw     219.87.3.247",
    "Registration Service Provider": "TWNIC",
    "Registration Service URL": "http://rs.twnic.net.tw/"
}

{
    'subject': [
        ('countryName', 'TW'),
        ('stateOrProvinceName', 'Taiwan'),
        ('localityName', 'Taipei'),
        ('organizationName', 'National Credit Card Center of R.O.C.'),
        ('commonName', 'www.nccc.com.tw')
    ],
    'issuer': [
        ('countryName', 'TW'),
        ('organizationName', 'TAIWAN-CA'),
        ('commonName', 'TWCA Secure SSL Certification Authority')
    ],
    'version': 3,
    'serialNumber': '47E800000007228F35337AC90ED23D36',
    'notBefore': 'Mar 31 22:59:32 2024 GMT',
    'notAfter': 'May  1 15:59:59 2025 GMT',
    'subjectAltName': [('DNS', 'www.nccc.com.tw')],
    'OCSP': ['http://twcasslocsp.twca.com.tw/'],
    'caIssuers': ['http://sslserver.twca.com.tw/cacert/secure_sha2_2023G3.crt'],
    'crlDistributionPoints': ['http://sslserver.twca.com.tw/sslserver/Securessl_revoke_sha2_2023G3.crl']
}
None
{'tel': '0800-058-085', 'addr': '臺北市松山區復興北路363號4樓'}



{
    "whois_data": {
        "Domain Name": "NVIDIA.COM",
        "Registry Domain ID": "4076489_DOMAIN_COM-VRSN",
        "Registrar WHOIS Server": "whois.safenames.net",
        "Registrar URL": "http://www.safenames.net",
        "Updated Date": "2024-04-22T00:57:07Z",
        "Creation Date": "1993-04-20T04:00:00Z",
        "Registrar Registration Expiration Date": "2025-04-21T04:00:00Z",
        "Registrar": "Safenames Ltd",
        "Registrar IANA ID": "447",
        "Registrar Abuse Contact Email": "abuse@safenames.net",
        "Registrar Abuse Contact Phone": "+44.1908200022",
        "Domain Status": "clientDeleteProhibited https://icann.org/epp#clientDeleteProhibited",
        "Registry Registrant ID": "Not Available From Registry",
        "Registrant Name": "Data protected, not disclosed",
        "Registrant Organisation": "NVIDIA Corporation",
        "Registrant Street": "Data protected, not disclosed",
        "Registrant City": "Data protected, not disclosed",
        "Registrant State/Province": "Data protected, not disclosed",
        "Registrant Postal Code": "Data protected, not disclosed",
        "Registrant Country": "US",
        "Registrant Phone": "Data protected, not disclosed",
        "Registrant Fax": "Data protected, not disclosed",
        "Registrant Email": "wadmpfvzi5ei@idp.email",
        "Registry Admin ID": "Not Available From Registry",
        "Admin Name": "International Domain Tech",
        "Admin Organisation": "Safenames Ltd",
        "Admin Street": "Linford Wood",
        "Admin City": "Milton Keynes",
        "Admin State/Province": "Bucks",
        "Admin Postal Code": "MK14 6LS",
        "Admin Country": "UK",
        "Admin Phone": "+44.1908200022",
        "Admin Fax": "+44.1908325192",
        "Admin Email": "hostmaster@safenames.net",
        "Registry Tech ID": "Not Available From Registry",
        "Tech Name": "International Domain Tech",
        "Tech Organisation": "Safenames Ltd",
        "Tech Street": "Linford Wood",
        "Tech City": "Milton Keynes",
        "Tech State/Province": "Bucks",
        "Tech Postal Code": "MK14 6LS",
        "Tech Country": "UK",
        "Tech Phone": "+44.1908200022",
        "Tech Fax": "+44.1908325192",
        "Tech Email": "hostmaster@safenames.net",
        "Name Server": "ns7.dnsmadeeasy.com",
        "DNSSEC": "unsigned",
        "URL of the ICANN WHOIS Data Problem Reporting System": "http://wdprs.internic.net/"
    },
    "ssl_cert_data": {
        "subject": [
            ["countryName", "US"],
            ["stateOrProvinceName", "California"],
            ["localityName", "Santa Clara"],
            ["organizationName", "NVIDIA Corporation"],
            ["commonName", "it.nvidia.com"]
        ],
        "issuer": [
            ["countryName", "US"],
            ["organizationName", "DigiCert Inc"],
            ["commonName", "DigiCert TLS RSA SHA256 2020 CA1"]
        ],
        "version": 3,
        "serialNumber": "0D542660A5DFAB260365CD7EA3F01495",
        "notBefore": "Aug 19 00:00:00 2024 GMT",
        "notAfter": "Aug 19 23:59:59 2025 GMT",
        "subjectAltName": [
            "it.nvidia.com",
            "*.download.nvidia.com",
            "*.mellanox.com",
            "*.nvidia.cn",
            "*.nvidia.com",
            "*.nvidia.partners",
            "*.nvw.nvidia.com",
            "*.order.store.nvidia.com",
            "*.stage.nvidia.com",
            "*.store.nvidia.com",
            "*.urm.nvidia.com",
            "*.urmstg.nvidia.com",
            "blogs.nvidia.co.jp",
            "blogs.nvidia.co.kr",
            "blogs.nvidia.com.tw",
            "layers.nvcr.io",
            "layers.stg.nvcr.io",
            "www.developer.nvidia.com",
            "www.frameswingames.com",
            "www.nvidia.com.ua",
            "www.openacc.org",
            "www.pgicompilers.com",
            "www.pgroup.com"
        ],
        "OCSP": [
            "http://ocsp.digicert.com"
        ],
        "caIssuers": [
            "http://cacerts.digicert.com/DigiCertTLSRSASHA2562020CA1-1.crt"
        ],
        "crlDistributionPoints": [
            "http://crl3.digicert.com/DigiCertTLSRSASHA2562020CA1-4.crl",
            "http://crl4.digicert.com/DigiCertTLSRSASHA2562020CA1-4.crl"
        ]
    }
}

"""




