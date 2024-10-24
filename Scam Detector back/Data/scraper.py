import re
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import threading

def close_driver(driver):
    driver.quit()

re_rules = {
        'addr': {'縣市': re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]{2}(市|縣)[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+[0-9]{1,3}\s?(號|號之\d+|之\d+號)\s?(\d+\s?樓|\d+\s?樓之\d+){0,1}'),}, 
        'tel': {'0800': re.compile(r'\b080(0|9)(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}\b'),
                '2-4-4': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}'),
                '2-3-4': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{4}'),
                '3-2-4': re.compile(r'(\(0\d{2}\)|0\d{2})(-| |&nbsp;)*\d{2}(-| |&nbsp;)*\d{4}'),
                '886': re.compile(r'\+?886(-| |&nbsp;)*\d(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}')},
        'phone': {'09': re.compile(r'(\(09\d{2}\)|09\d{2})(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}'),
                  '0809': re.compile(r'0809(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}')},
        'fax': {'fax': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}')},
        'num': {'num': re.compile(r'\d{8}'),},
        'mail': {'email': re.compile(r'[A-Za-z][a-zA-Z\-\.]+@([a-zA-Z\-]+\.)+[a-zA-Z\-]{2,4}')},
        'Food Business Registration No.': {'food': re.compile(r'[A-Z]-\d{9,9}-\d{5,5}-\d')}
    }
         
            
def extract_info(category: str, html: list[str]):     
    result = []
    for _, regex in re_rules[category].items():
        for line in html:
            match_obj = regex.search(line)
            if match_obj:
                result.append(match_obj.group(0))
    return result

keys = {
        'addr': ['市', '縣'], 
        'tel': ['客服', '專線', '電話', '市話', '聯繫'],
        'phone': ['手機'],
        'fax': ['傳真', 'fax', 'Fax', '聯繫'],
        'num': ['統編', '統一編號'],
        'mail': ['信箱', 'mail', 'email', '郵件', '聯繫'],
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
    
    matches = re.findall(key, html)

    for match in matches:
        try:
            match_start_index = html.index(match)
        except ValueError:
            # Handle the case where the match is not found
            match_start_index = -1  # or some other appropriate value
            # You might also want to log this or take some other action
        
        valid_content = html[match_start_index-2:]
        lines = valid_content.splitlines()
        
        retv = None
        if len(lines) < 4:
            retv = extract_info(category, lines)
        else:
            retv = extract_info(category, lines[:4])
            
        if retv:
            if category not in info:
                info[category] = []
            # Add deduplication when extending the list
            info[category].extend(list(set(retv)))
        else:
            info['null'] = 'NULL'
    
    return info
    
def scraper(url:str): 
    if not re.match(r'https://|http://', url):
        raise('Scraper cannot handle url format')
    
    try:
        # driver settings -> do not load images and use headless mode
        chromeOpt = webdriver.ChromeOptions()
        chromeOpt.add_argument("--headless=new")  # Updated headless flag
        chromeOpt.add_argument("--disable-gpu")
        chromeOpt.add_argument("--no-sandbox")
        chromeOpt.add_argument("--disable-dev-shm-usage")
        chromeOpt.add_argument('--blink-settings=imagesEnabled=false')
        
        driver = webdriver.Chrome(options=chromeOpt)
        driver.get(url)
        
        info = {}
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        threading.Thread(target=close_driver, args=(driver,)).start()
        
        # grab footer from the page
        footer_element = [soup.find('footer')]
        footer = []
        
        # check if footer_element[0] is none
        if not footer_element[0]:
            # find element with class or id include footer, because it may appear in many places, so don't grab the element following it
            footer_class_element = soup.find_all(class_=re.compile('footer'))
            footer_id_element = soup.find_all(id=re.compile('footer'))
            
            footer_element = list(set(footer_class_element + footer_id_element))
        else:
            # add the element below footer element
            footer_sibling =  [elem.find_next_siblings() for elem in footer_element]
            
            for elem in footer_sibling:
                footer = footer + [e for e in elem]
                            
        footer = footer_element + footer
        footer = ' '.join([elem.get_text() for elem in list(set(footer))])
 
        if not footer:
            print("No footer found!")
            return {}

        with ThreadPoolExecutor(max_workers=18) as executor:
            futures = [executor.submit(process_footer_element, footer, index) for index in range (18)]
            for future in as_completed(futures):
                element_info = future.result()
                if element_info:  # Check if element_info is not empty
                    key, value = next(iter(element_info.items()))  # Get the single key-value pair
                    if key in info:
                        info[key] = list(set(info[key] + value))
                    else:
                        info[key] = value
                    
        if 'null' in info:
            info.pop('null')
            
        for category in info:
            if isinstance(info[category], list):
                info[category] = list(dict.fromkeys(info[category]))
        
        return info
    
    except Exception as e:
        print('Exception:', e)
        threading.Thread(target=close_driver, args=(driver,)).start()
        return {}

# matchList = None    
# try:
#     matchList = scraper("https://www.momoshop.com.tw/main/Main.jsp") # momo 1min -> 40sec -> 8
#     #matchList = scraper("https://www.gvm.com.tw/") # 遠見雜誌 43sec -> 29sec -> 5
#     #matchList = scraper("https://www.cht.com.tw/home/consumer") # 中華電信 43sec -> 29sec -> 8
#     #matchList = scraper("https://www.bnext.com.tw/") # 數位時代47sec -> 23sec -> 6
#     #matchList = scraper("https://www.nccc.com.tw/wps/wcm/connect/zh/home") # 財團法人聯合信用卡處理中心全球資訊網 30sec -> 20sec -> 4
#     #matchList = scraper("https://www.104.com.tw/jobs/main/", driver) # 104 30sec -> 22sec -> 4
#     #matchList = scraper("https://www.591.com.tw/", driver) # 591 86sec -> 50sec -> 4
#     print(matchList)
    
# except Exception as e:
#     pass

if __name__ == "__main__":
    print(scraper("https://www.dbs.com.tw/personal-zh/default.page"))
