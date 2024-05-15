import re
import multiprocess
import dill
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException

def match_regex(key:str, webElement, index:int, driver):
    #print(f'Detacting {key}')
    #print(webElement.text)
    re_rules = {
        'addr': {'縣市': re.compile(r'(.*\n)?.{2}(市|縣).+(號|號之\d+)(\d+樓|\d+樓之\d+)?'),}, 
        'tel': {'0800': re.compile(r'\b080(0|9)(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}\b'),
                '2-4-4': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}'),
                '2-3-4': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{4}'),
                '3-2-4': re.compile(r'(\(0\d{2}\)|0\d{2})(-| |&nbsp;)*\d{2}(-| |&nbsp;)*\d{4}'),
                '886': re.compile(r'\+?886(-| |&nbsp;)*\d(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}')}, # 886-2-00000000
        'phone': {'09': re.compile(r'(\(09\d{2}\)|09\d{2})(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}'),
                  '0809': re.compile(r'0809(-| |&nbsp;)*\d{3}(-| |&nbsp;)*\d{3}')},
        'fax': {'fax': re.compile(r'(\(0\d\)|0\d)(-| |&nbsp;)*\d{4}(-| |&nbsp;)*\d{4}')},
        'num': {'num': re.compile(r'\d{8}'),},
        'mail': {'email': re.compile(r'[\w\-\.]+@([\w\-]+\.)+[\w\-]{2,4}'),},
        'company': {'公司': re.compile(r'[^0-9 \n\ta-zA-Z><?!@#$%\^&*"\'\\~`]+股份有限公司')},
        'Food Business Registration No.': {'food': re.compile(r'[A-Z0-9-]')}
        #'other': {},
    }
    
    match = None
    try:
        for _, regex in re_rules[key].items():
            match_obj = regex.search(webElement.text)
            if match_obj:
                match = match_obj.group(0)
                return match
                    
        following_siblings = webElement.find_elements(By.XPATH, "following-sibling::*")
        for element in following_siblings[:3]:
            for _, regex in re_rules['tel'].items():
                match_obj = regex.search(element.text)            
                if match_obj:
                    match = match_obj.group(0)
                    return match
                
    except StaleElementReferenceException as e:
        we = driver.find_elements(By.XPATH, '//footer//*[text()]') +\
            driver.find_elements(By.XPATH, "//*[contains(@class, 'footer')]//*[text()]")
        we = we[index]
        return match_regex(key, we, index, driver)
            
    return match
            
            
def extract_info(category: str, key: str, webElement, index:int, driver):      
    result = None
    match category:
        case 'addr': 
            if key == '市' or key == '縣':
                result = match_regex('addr', webElement, index, driver)
        case 'tel': 
            if key in ['客服', '專線', '電話', '市話', '專線']:
                result = match_regex('tel', webElement, index, driver)
        case 'phone': 
            if key == '手機':
                result = match_regex('phone', webElement, index, driver)
        case 'fax': 
            if key in ['傳真', 'fax', 'Fax']:
                result = match_regex('fax', webElement, index, driver)
        case 'num': 
            if key in ['統編', '統一編號']:
                result = match_regex('num', webElement, index, driver)
        case 'mail': 
            if key in ['信箱', 'mail', 'email', '郵件']:
                result = match_regex('mail', webElement, index, driver)
        case 'company': 
            if key in ['股份有限公司', '營業人', '經營者']:
                result = match_regex('company', webElement, index, driver)
        case 'Food Business Registration No.': 
            if key == '食品業':
                result = match_regex('Food Business Registration No.', webElement, index, driver)
        #case 'other': 
        #    if key in ['意見反映', '關於我們', '聯絡我們']:
        #        result = match_regex('other', webElement, index, driver)
        
    return result
'''
def iterate_webelement(webElement):
    info = {}
    if webElement:
        for category, keywords in keys.items():
            for elmt in webElement:
                if elmt.tag_name not in ['a', 'img', 'script']:
                    find = False
                    for key in keywords:
                        if key in elmt.text:
                            find = True
                            info[category] = extract_info(category, key, elmt)
                            break
                    if find: break
    else:
        print("Footer is empty.")
        return None
    
    return info
'''
def scraper(url:str):
    firefoxOpt = Options()
    firefoxOpt.add_argument("-headless")
    '''options=firefoxOpt'''
    #firefoxOpt.add_argument("user-agent=haha")
    driver = webdriver.Firefox(options=firefoxOpt)
    
    if not re.match(r'https://|http://', url):
        raise('Scraper cannot handle url format')
    
    info = {}
    
    try:
        driver.get(url)
        
        # list of footers and elements with 'footer' substring inside their class attribute 
        footers = driver.find_elements(By.XPATH, '//footer//*[text() and not(self::a)]') +\
            driver.find_elements(By.XPATH, "//*[contains(@class, 'footer')]//*[text() and not(self::a)]")

        #footer_list = []
        keys = {
            'addr': ['市', '縣'], 
            'tel': ['客服', '專線', '電話', '市話', '專線'],
            'phone': ['手機'],
            'fax': ['傳真', 'fax', 'Fax'],
            'num': ['統編', '統一編號'],
            'mail': ['信箱', 'mail', 'email', '郵件'],
            'company': ['股份有限公司', '營業人', '經營者'],
            'Food Business Registration No.': ['食品業']
            #'other': ['意見反映', '關於我們', '聯絡我們'],
        }
        
        for index, footer_elements in enumerate(footers):
            if footer_elements:                
                #find all elements under the footer_elementss of footer        
                if isinstance(footer_elements, list):
                    for category, keywords in keys.items():
                        for elmt in footer_elements:
                            print(elmt.text)
                            find = False
                            for key in keywords:
                                if key in elmt.text:
                                    find = True
                                    retv = extract_info(category, key, elmt, index, driver)
                                    if retv:
                                        info[category] = retv
                                    break
                            if find: break
                else:
                    for category, keywords in keys.items():
                        for key in keywords:
                            if key in footer_elements.text:
                                find = True
                                retv = extract_info(category, key, footer_elements, index, driver)
                                if retv:
                                    info[category] = retv
                                break
            else:
                print("Footer is empty.")
                return None
        '''       
        with multiprocess.Pool(processes=50) as pool:
            results = pool.map(func=iterate_webelement, iterable=(footer_list,))
        print(results)
              '''  
        return info
    except ConnectionAbortedError as e:
        print("Connection error in scraper: ", e)
    
    except StaleElementReferenceException as e:
        print("Stale element reference in scraper: ", e)
        
    except Exception as e:
        print("Unknown error in scraper: ", e)
        
    finally:
        driver.quit()

#matchList = scraper("https://www.momoshop.com.tw/main/Main.jsp") # momo 1min
#matchList = scraper("https://www.gvm.com.tw/") # 遠見雜誌 43sec
#matchList = scraper("https://www.cht.com.tw/home/consumer") # 中華電信 43sec
#matchList = scraper("https://www.bnext.com.tw/") # 數位時代47sec
matchList = scraper("https://www.nccc.com.tw/wps/wcm/connect/zh/home") # 財團法人聯合信用卡處理中心全球資訊網 30sec
#matchList = scraper("https://www.104.com.tw/jobs/main/") # 104 30sec
#matchList = scraper("https://www.591.com.tw/") # 591 86sec
    
print(matchList)