import re
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

re_rules = {
        'addr': {'縣市': re.compile(r'[^A-Za-z!@#$%^&*()_+1234567890=?/;:{}<>,.~`-]{2}(市|縣)[^A-Za-z!@#$%^&*()_+1234567890=?/;:{}<>,.~`-]+[0-9]{1,3} ?(號|號之\d+|之\d+號) ?(\d+ ?樓|\d+ ?樓之\d+){0,1}'),}, 
        'tel': {'0800': re.compile(r'\b080(0|9)(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}\b'),
                '2-4-4': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}'),
                '2-3-4': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{4}'),
                '3-2-4': re.compile(r'(\(0\d{2}\)|0\d{2})(-| |&nbsp;)*\d{2}(-| |&nbsp;)*\d{4}'),
                '886': re.compile(r'\+?886(-| |&nbsp;)*\d(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}')},
        'phone': {'09': re.compile(r'(\(09\d{2}\)|09\d{2})(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}'),
                  '0809': re.compile(r'0809(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}')},
        'fax': {'fax': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}')},
        'num': {'num': re.compile(r'\d{8}'),},
        'mail': {'email': re.compile(r'[A-Za-z][\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}'),},
        'Food Business Registration No.': {'food': re.compile(r'[A-Z]-\d{9,9}-\d{5,5}-\d')}
    }
         
            
def extract_info(category: str, html: list[str]):     
    if category == 'num':
        pass
             
    result = None
    for _, regex in re_rules[category].items():
        for line in html:
            match_obj = regex.search(line)
            if match_obj:
                result = match_obj.group(0)
                return result                
            
    return result

keys = {
            'addr': ['市', '縣'], 
            'tel': ['客服', '專線', '電話', '市話', '專線'],
            'phone': ['手機'],
            'fax': ['傳真', 'fax', 'Fax'],
            'num': ['統編', '統一編號'],
            'mail': ['信箱', 'mail', 'email', '郵件'],
            'Food Business Registration No.': ['食品業']
        }

def process_footer_element(html: str, key_index):
    info = {}
    category = None
    key = None
    match key_index:
        case 0: 
            key = keys['addr'][0]
            category = 'addr'
        case 1: 
            key = keys['addr'][1]
            category = 'addr'
        case 2: 
            key = keys['tel'][0]
            category = 'tel'
        case 3: 
            key = keys['tel'][1]
            category = 'tel'
        case 4: 
            key = keys['tel'][2]
            category = 'tel'
        case 5: 
            key = keys['tel'][3]
            category = 'tel'
        case 6: 
            key = keys['tel'][4]
            category = 'tel'
        case 7: 
            key = keys['phone'][0]
            category = 'phone'
        case 8: 
            key = keys['fax'][0]
            category = 'fax'
        case 9: 
            key = keys['fax'][1]
            category = 'fax'
        case 10: 
            key = keys['fax'][2]
            category = 'fax'
        case 11: 
            key = keys['num'][0]
            category = 'num'
        case 12: 
            key = keys['num'][1]
            category = 'num'
        case 13: 
            key = keys['mail'][0]
            category = 'mail'
        case 14: 
            key = keys['mail'][1]
            category = 'mail'
        case 15: 
            key = keys['mail'][2]
            category = 'mail'
        case 16: 
            key = keys['mail'][3]
            category = 'mail'
        case 17: 
            key = keys['Food Business Registration No.'][0]
            category = 'Food Business Registration No.'
    
    if key == "市":
        pass 
    
    matches = re.finditer(key, html)

    for match in matches:
        match_start_index = match.start()
        valid_content = html[match_start_index:]
        lines = valid_content.splitlines()
        
        retv = None
        if 4 > len(lines):
            retv = extract_info(category, lines)
        else:
            retv = extract_info(category, lines[:4])
            
        if retv:
            info[category] = retv
        else:
            info['null'] = 'NULL'
    
    return info
    
def scraper(url:str, driver: webdriver): 
    if not re.match(r'https://|http://', url):
        raise('Scraper cannot handle url format')
    
    info = {}
    driver.get(url)
    html = driver.page_source
    start_index = html.find('footer')
    
    if start_index != -1:
        footer = html[start_index:]
    else:
        print("No footer found!")
        exit(1)

    with ThreadPoolExecutor(max_workers=18) as executor:
            futures = [executor.submit(process_footer_element, footer, index) for index in range (18)]
            for future in as_completed(futures):
                element_info = future.result()
                info.update(element_info)
    if 'null' in info:
        info.pop('null')
    return info
        
   
start = time.time()
chromeOpt = webdriver.ChromeOptions()
chromeOpt.add_argument("-headless")
chromeOpt.add_argument('--blink-settings=imagesEnabled=false')
driver = webdriver.Chrome(options=chromeOpt)

matchList = None    
try:
    #matchList = scraper("https://www.momoshop.com.tw/main/Main.jsp", driver) # momo 1min -> 40sec -> 8
    #matchList = scraper("https://www.gvm.com.tw/", driver) # 遠見雜誌 43sec -> 29sec -> 5
    #matchList = scraper("https://www.cht.com.tw/home/consumer", driver) # 中華電信 43sec -> 29sec -> 8
    #matchList = scraper("https://www.bnext.com.tw/", driver) # 數位時代47sec -> 23sec -> 6
    #matchList = scraper("https://www.nccc.com.tw/wps/wcm/connect/zh/home", driver) # 財團法人聯合信用卡處理中心全球資訊網 30sec -> 20sec -> 4
    #matchList = scraper("https://www.104.com.tw/jobs/main/", driver) # 104 30sec -> 22sec -> 4
    #matchList = scraper("https://www.591.com.tw/", driver) # 591 86sec -> 50sec -> 4
    print(matchList)
    end = time.time()
    print("The time of execution of above program is :",
      (end-start), "s")
    
finally:
    if driver:
        driver.quit()