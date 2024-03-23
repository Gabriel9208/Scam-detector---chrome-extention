import requests
import socket
from sys import exit
import json
import re

def grab_domain(url:str) -> str:
    # process start
    match = re.search(r'^http(s?)://', url)
    domain = ""
    if match:
        domain = url.split('/')[2]
    else:
        domain = url    
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

    # Extract whois content for later use
    delete_head = first_req.text.find("Domain Name: ")
    black_list = ["</div>", "</pre>", "&gt;&gt;"]
    find_tail = [first_req.text[delete_head:].find(key) for key in black_list]
    delete_tail = min([i + delete_head for i in find_tail if i != -1])
    return_data = first_req.text[delete_head: delete_tail]
    
    # extracting whois_server and registrar from the response 
    data = return_data.split('\n')
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
        print("Using https://www.whois.com/whois/imeifoods.com.tw: ")
    else:
        # take the ending '\n' off of the string to prevent '[Errno 11001] getaddrinfo failed'
        registrar_whois = registrar_whois.strip()
        #print(registrar_whois)
    
    return registrar_whois, new_domain, return_data

def second_level_search(registrar_whois:str, query_domain:str) -> str:
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
        print("TCP connection failed", e)
        exit(1)

    TCP_socket.close()
    
    #filter the output
    resp = str()
    for line in temp:
        if '>' in line:
            break
        resp += line
        
    return resp
            
# take \r\n in the response message off
def CRLF_take_off(data:str) -> str:
    buf = str()
    for item in data.strip('\r\n').split('\r\n'):
        buf += item + '\n'
    return buf

# turn a piece of data into JAON format
def combine_json(title:str, data:str) -> str:
    buffer = str()
    counter = 0
    if title == 'other':
        for line in data.split('\n'):
            if line.split(":")[0] == "":
                buffer = re.sub(r',\s*$', '', buffer)
                break
            # key with no value
            if len(line.split(":")) == 1:
                buffer += f'"{line.split(":")[0].strip()}": "",\n'
            else:
                buffer += f'"{line.split(":")[0].strip()}": "{line.split(":")[1].strip()}",\n'
        buffer += ',\n'
    else:
        buffer = f'"{title}": ' + '{\n'
            
        for line in data.split('\n'):
            if line == "":
                continue
            if ':' not in line:
                buffer += f'"{title}_{counter}": "{line}",\n'
                counter += 1 
            elif line.split(":")[0] == "":
                buffer = re.sub(r',\s*$', '', buffer)
                break
            elif len(line.split(":")) == 1:
                buffer += f'"{line.split(":")[0]}": "",\n'
            else:
                buffer += f'"{line.split(":")[0]}": "{line.split(":")[1].strip()}",\n'
                
        buffer = re.sub(r',\s*$', '', buffer)
        buffer += '},\n'
    
    #print(buffer)
    return buffer
    
    
def padding_handler(data:str) -> str:
    '''
    remove padding:
    
    original format:
        registrant:
            aaa
            
    turn into: 
        registrant: aaa
    '''
    
    pre = "" # previous line
    for line in data.split('\n'):
        if line == "":
            continue
        if '<' in line or '>' in line:
            data = data.replace(line + '\n', "")
            continue
        if ":" in line and line.split(":")[1] != "":
            pre = ""
            continue
        elif ":" in line and line.split(":")[1] == "":
            pre = line
            continue
        elif pre != "" and ":" not in line:
            index = data.find(pre + '\n' + line)
            if index != -1:
                data = data.replace(pre + '\n' + line, pre + line)
            else:
                data = data.replace(line, pre + line, 1)
    #print(data)
    return data
    
# hold the full process for converting data into JSON format
def to_json(data:str):
    data = CRLF_take_off(data)
    data = padding_handler(data)
    # check weather data can be processed
    filter = ['Error', 'error', 'Not', 'not']
    for word in filter:
        if word in data:
            return data
    if data == '\n' or data == '' or data == ' ':
        return data
    
    keyword = ['Registrar', 'Registrant', 'Admin', 'Tech', 'Name Server', 'other']
    content = {'Registrar': "", 'Registrant': "", 'Admin': "", 'Tech': "", 'Name Server': "", 'other': ""}
    
    # package into different categories
    for key in keyword:
        for line in data.split('\n'):
            if key in line:
                if key == 'Name Server':
                    content[key] += line.strip().split(':')[1].strip() + '\n'
                else:
                    add = line.strip()[len(key) + 1:].strip()
                    if ':' not in add:
                        content[key] += line.strip()[len(key) + 1:].strip() + '\n'
                    else:
                        content[key] += line.strip()[len(key) + 1:].strip() + '\n'
                data = data.replace(line + '\n', "")
    content['other'] = data
    
    # transform JSON-like format
    final_json = '{\n'
    for key in keyword:
        final_json += combine_json(key, content[key])
    final_json = re.sub(r',\s*$', '', final_json)
    final_json += '}\n'
    
    #print(final_json)
    final_json = json.loads(final_json)
    return final_json

def search_whois(url:str):
    domain = grab_domain(url)
    whois, domain, content = first_level_search(domain)
    data = None
    if whois:
        data = second_level_search(whois, domain)
    else: 
        data = content
    # data in json format
    data = to_json(data)
    #print(data)
    return data

#search_whois("breathcenter.com")
#https://www.imeifoods.com.tw/