import asyncio
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException

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
}

keys = {
        'addr': ['市', '縣'], 
        'tel': ['客服', '專線', '電話', '市話', '專線'],
        'phone': ['手機'],
        'fax': ['傳真', 'fax', 'Fax'],
        'num': ['統編', '統一編號'],
        'mail': ['信箱', 'mail', 'email', '郵件'],
        'company': ['股份有限公司', '營業人', '經營者'],
    }

def match_regex(key:str, webElement):
    print(f'Detacting {key}')
    
    match = None
    for _, regex in re_rules[key].items():
        match_obj = regex.search(webElement.text)
        if match_obj:
            match = match_obj.group(0)
            return match
                
    following_siblings =  webElement.find_elements(By.XPATH, "following-sibling::*")
    for element in following_siblings[:3]:
        for regex in re_rules['tel']:
            match_obj = regex.search(element.text)            
            if match_obj:
                match = match_obj.group(0)
                return match
            
    return match
            
            
def extract_info(category: str, key: str, webElement):      
    result = None
    match category:
        case 'addr': 
            if key == '市' or key == '縣':
                result = match_regex('addr', webElement)
        case 'tel': 
            if key in ['客服', '專線', '電話', '市話', '專線']:
                result = match_regex('tel', webElement)
        case 'phone': 
            if key == '手機':
                result = match_regex('phone', webElement)
        case 'fax': 
            if key in ['傳真', 'fax', 'Fax']:
                result = match_regex('fax', webElement)
        case 'num': 
            if key in ['統編', '統一編號']:
                result = match_regex('num', webElement)
        case 'mail': 
            if key in ['信箱', 'mail', 'email', '郵件']:
                result = match_regex('mail', webElement)
        case 'company': 
            if key in ['股份有限公司', '營業人', '經營者']:
                result = match_regex('company', webElement)
        
    return result

async def scrape_footer_elements(footer_elements):    
    #find all elements under the footer_elementss of footer
    print("scrape_footer_elements1")
    inside_elements = footer_elements.find_elements(By.XPATH, r'//*')
    print("scrape_footer_elements2")
    info = {}
    if inside_elements:
        for category, keywords in keys.items():
            for elmt in inside_elements:
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
    return info
    

async def async_scraper(url:str):
    firefoxOpt = Options()
    firefoxOpt.add_argument("-headless")
    '''options=firefoxOpt'''
    firefoxOpt.add_argument("user-agent=haha")
    driver = webdriver.Firefox(options=firefoxOpt)
    
    if not re.match(r'https://|http://', url):
        print('Scraper cannot handle url format.')
        exit(1)
    
    try:
        driver.get(url)

        # list of footers and elements with 'footer' substring inside their class attribute         
        footer_num = len(driver.find_elements(By.TAG_NAME, 'footer')) + len(driver.find_elements(By.XPATH, "//*[contains(@class, 'footer')]"))
        tasks = []
        for index in range(footer_num):
            # Prevent StaleElementReferenceException
            footer_elements = driver.find_element(By.TAG_NAME, 'footer') if index == 0 else \
                                            driver.find_elements(By.XPATH, "//*[contains(@class, 'footer')]")[index - 1]
            task = asyncio.create_task(scrape_footer_elements(footer_elements))     
            tasks.append(await task)
                
        results = await asyncio.gather(*tasks)
        return results
    
    except ConnectionAbortedError as e:
        print("Connection error in scraper: ", e)
    except StaleElementReferenceException as e:
        print("Stale element reference in scraper: ", e)
    except Exception as e:
        print("Unknown error in scraper: ", e)
    finally:
        driver.quit()

async def main():
    matchList = await async_scraper("https://www.bnext.com.tw/")
    print(matchList)
    '''
    matchList = scraper("https://www.bnext.com.tw/")
    print(matchList)
    '''

asyncio.run(main())