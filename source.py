from whoisInfo import search_whois
from TLS_check import fetch_tls_cert
from findbiz import findbiz
from scraper import scraper
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

html_front = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
<p>
'''
html_back = '''</p>
</body>
</html>'''

in_url = input("Enter url: ")
result = []

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(findbiz, in_url), 
               executor.submit(scraper, in_url),
               executor.submit(search_whois, in_url), 
               executor.submit(fetch_tls_cert, in_url),]
    
    for future in as_completed(futures):
        result.append(future.result())

whois = None
tls = None
biz = None
con = None

for i in result:
    match classify(i):
        case 'whois': whois = i
        case 'tls': tls = i
        case 'biz': biz = i
        case 'con': con = i

whoisSection = ""
tlsSection = ""
biz = ""
con = ""





