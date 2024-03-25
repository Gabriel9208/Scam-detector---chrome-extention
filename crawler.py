from selenium import webdriver
import re

def crawler(url:str, driver:webdriver.Firefox):
    if not re.match(r'https://|http://', url):
        raise('Crawler cannot handle url format')
    
    try:
        driver.get(url)
        html = driver.page_source
        links = re.findall(r'\b(?:https?|ftp):\/\/[-A-Za-z0-9+&@#\/%?=~_|!:,.;]*[-A-Za-z0-9+&@#\/%=~_|]', html)
        return True, links
    
    except ConnectionError as e:
        print("Connection error in crawler: ", e)
    except Exception as e:
        print("Unknown error in crawled: ", e)
    return False, []

def scraper(url:str ,driver:webdriver.Firefox):
    # todo
    if not re.match(r'https://|http://', url):
        raise('Scraper cannot handle url format')
    
    addrKey = ['address', 'Address', 'ADDRESS', 'location', 'Location', 'LOCATION', '地址', '地理位址', '位置', '地理位置']
    
    try:
        driver.get(url)
        #
    except ConnectionAbortedError as e:
        print("Connection error in scraper: ", e)
    except Exception as e:
        print("Unknown error in scraper: ", e)
    #.find_element(By.TAG_NAME, 'a').get_attribute('href')
    
def manager(urls:list):
    driver = webdriver.Firefox()
    driver.implicitly_wait(5)
    
    worklist = {}
    for u in urls:
        # 0 -> not crawled/scraped
        # -1 -> error
        worklist[u] =  0
    
    # crawl
    crawling = True
    while crawling:
        newDisplore = {}
        for url, flag in worklist.items():
            if flag == 1 or flag < -1:
                continue
            
            success, newUrl = crawler(url, driver)
            
            if success:
                # add new url
                for nu in newUrl:
                    if nu not in worklist and nu not in newDisplore:
                        newDisplore[nu] = 0
                        
                # mark as scuuess
                worklist[url] = 1
            else:
                #mark as error
                worklist[url] -= 1
                
        # guarantee all values to be either error or success
        crawling = False
        for i in worklist.values():
            if i == 0 or i == -1:
                crawling = True
                continue
    
    # set all flags to 0 -> ready to scrape
    for url in worklist:
        worklist[url] = 0
    
    # scrape
    scraping = True
    while scraping:
        for url, flag in worklist:
            if flag == 1 or flag < -1:
                continue
            
            success = scraper(url)
            
            if success:
                worklist[url] = 1
            else:
                worklist[url] -= 1
                
        crawling = False
        for i in worklist.values():
            if i == 0 or i == -1:
                crawling = True
                continue
            
# Just for testing
a = ["https://www.nvidia.com/zh-tw/"]
manager(a)