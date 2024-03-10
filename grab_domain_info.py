import requests
import socket
from sys import exit
import json
import re

def grab_domain() -> str:
    # process start
    print("""
_|          _|  _|    _|    _|_|    _|_|_|    _|_|_|          (\__/)
_|          _|  _|    _|  _|    _|    _|    _|               /      \\
_|    _|    _|  _|_|_|_|  _|    _|    _|      _|_|          /   o o  \\
  _|  _|  _|    _|    _|  _|    _|    _|          _|        \    ^    /
    _|  _|      _|    _|    _|_|    _|_|_|  _|_|_|           \  ---  / 
                                                              --------
                                                              (  ? ? )
""")
    domain = input("(Enter domain name or ip address)\nWHO IS ")
    return domain



def first_level_search(query_domain:str) -> str:
    # make GET request to whois_url
    whois_url = "https://www.whois.com/whois"
    req_url = whois_url + '/' + query_domain
    try:
        first_req = requests.get(req_url)
    except requests.exceptions.RequestException as e:
        print(e)
        exit(1)

    # extracting whois_server and registrar from the response 
    data = first_req.text.split('\n')
    registrar_whois = None
    new_domain = None
    for line in data:
        if "Registrar WHOIS Server: " in line:
            if 'http' in line:
                # Two kinds: "http://google.com" or "google.com"
                registrar_whois = line[24:].split('/')[2] 
            else:
                registrar_whois = line[24:]
        elif "Domain Name: " in line:
            match = re.search(r'Domain Name: (.+)$', line)
            if match:
                new_domain = match.group(1)
            else:
                print("No Domain Name found.") 
                exit(0)               
            
    if registrar_whois is None:
        print("Domain:", query_domain, " registrar WHOIS server can not be found.")
        exit(0)

    # take the ending '\n' off of the string to prevent '[Errno 11001] getaddrinfo failed'
    registrar_whois = registrar_whois.strip()
    #print(registrar_whois)
    
    return registrar_whois + ' ' + new_domain

def con_reg_whois(registrar_whois:str, query_domain:str) -> str:
    # create socket to communicate with the whois server
    TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    registrar_addr = (registrar_whois, 43)
    try:
        TCP_socket.connect(registrar_addr)
        # query the target domain to the registrar whois server
        query = query_domain + "\r\n"
        TCP_socket.sendall(query.encode())
        
        # receive
        resp = b''
        while True:
            rec = TCP_socket.recv(2048)
            if not rec:
                break
            resp += rec
        temp = resp.decode()
        #print(temp)
        
    except Exception as e:
        print("Line 81: ", e)
        exit(1)

    #filter the output
    resp = str()
    for line in temp:
        if '>' in line:
            break
        resp += line
        
    return resp
            
# take \r\n in the response message off
def data_preprocess(data:str) -> str:
    buf = str()
    for item in data.strip('\r\n').split('\r\n'):
        buf += item + '\n'
    return buf

# turn a piece of data into JAON format
def combine_json(title:str, data:str) -> str:
    buffer = str()
    if title == 'other':
        for line in data.split('\n'):
            if line.split(":")[0] == "":
                buffer = re.sub(r',\s*$', '', buffer)
                break
            # key with no value
            if len(line.split(":")) == 1:
                buffer += f'"{line.split(":")[0]}": "",\n'
            else:
                buffer += f'"{line.split(":")[0]}": "{line.split(":")[1].strip()}",\n'
        buffer += ',\n'
    else:
        buffer = f'"{title}": ' + '{\n'
        for line in data.split('\n'):
            if line.split(":")[0] == "":
                buffer = re.sub(r',\s*$', '', buffer)
                break
            if len(line.split(":")) == 1:
                buffer += f'"{line.split(":")[0]}": "",\n'
            else:
                buffer += f'"{line.split(":")[0]}": "{line.split(":")[1].strip()}",\n'
        buffer += '},\n'
    
    #print(buffer)
    return buffer
    
# hold the full process for converting data into JSON format
def to_json(data:str) -> str:
    data = data_preprocess(data)
    # check weather data can be processed
    filter = ['Error', 'error', 'Not', 'not']
    for word in filter:
        if word in data:
            return data
    if data == '\n' or data == '' or data == ' ':
        return data
    reg_rar = str()
    reg_ant = str()
    admin = str()
    tech = str()
    name_serv = str()
    other = str()
    for line in data.split('\n'):
        if 'Registrar' in line:
            reg_rar += line.strip()[10:] + '\n'
        elif 'Registrant' in line:
            reg_ant += line.strip()[11:] + '\n'
        elif 'Admin' in line:
            admin += line.strip()[6:] + '\n'
        elif 'Tech' in line:
            tech += line.strip()[5:] + '\n'
        elif 'Naame Server' in line:
            name_serv += line.strip().split(':')[1].strip() + '\n'
        else:
            other += line + '\n'
    final_json = '{\n'
    final_json += combine_json('Registrar', reg_rar)
    final_json += combine_json('Registrant', reg_ant)
    final_json += combine_json('Admin', admin)
    final_json += combine_json('Tech', tech)
    final_json += combine_json('other', other)
    final_json = re.sub(r',\s*$', '', final_json)
    final_json += '}\n'
    #print(final_json)
    final_json = json.loads(final_json)
    return final_json

domain = grab_domain()
whois = first_level_search(domain)
data = con_reg_whois(whois.split()[0], whois.split()[1])
# data in json format
data = to_json(data)
print(data)