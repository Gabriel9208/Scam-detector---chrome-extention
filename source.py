from whoisInfo import search_whois
from TLS_check import tls_cert
from findbiz import findbiz
from scraper import scraper
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def classify(obj) -> str:
    if not obj:
        return 'Not found'
    
    if 'subject' in obj:
        return 'tls'
    elif 'Registrar' in obj:
        return 'whois'
    elif type(obj) == list:
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
start = time.time()
result = []

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(findbiz, in_url), 
               executor.submit(scraper, in_url),
               executor.submit(search_whois, in_url), 
               executor.submit(tls_cert, in_url),]
    
    for future in as_completed(futures):
        result.append(future.result())

close = time.time()

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

print(close - start)
print(1)
print(whois)
print(2)
print(tls)
print(3)
print(biz)
print(4)
print(con)