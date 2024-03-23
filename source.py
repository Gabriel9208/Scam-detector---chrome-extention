import whoisInfo as whois
import TLS_check as tls

url = input("Enter url: ")
whois_info = whois.search_whois(url)
cert_info = tls.tls_cert(url)
print(whois_info)
print(cert_info)