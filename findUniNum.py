import re
from sys import exit
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

def findUni(coName:str):
    if not coName:
        raise ValueError("Company name cannot be empty. Maybe error parsing the url.")
    
    uniNum = ""

    firefoxOpt = Options()
    firefoxOpt.add_argument("-headless")

    '''options=firefoxOpt'''
    driver = webdriver.Firefox()
    driver.implicitly_wait(5)
    try:
        driver.get('https://www.google.com/')
        searchBar = driver.find_element(By.NAME, "q")
        searchBar.send_keys(f"{coName} 公司統編")
        searchBar.send_keys(Keys.ENTER)
        
        # get link
        links = driver.find_elements(By.CLASS_NAME, 'yuRUbf')
        if not links:
            raise NoSuchElementException("Link search results not found.")
        
        match = None
        for i in range(len(links)):
            if i > 1:
                raise ValueError('統編 is not found.')
            driver.get(links[i].find_element(By.TAG_NAME, 'a').get_attribute('href'))
            html = driver.page_source
            driver.back()
            links = driver.find_elements(By.CLASS_NAME, 'yuRUbf')

            # print(html)
            match = re.findall(r'(?:統編|統一編號)(?:<\/b> :<\/td> <td colspan="2">|:|.*)\d{8}', html)
            if match:
                break
        if not match:
            raise ValueError('統編 is not found.')
        
        uniNum = match[0][-8:]
        return uniNum
        
    except NoSuchElementException as e:
        print("Search bar is not found:", e)
                
    except Exception as e:
        print(e)
    finally:
        driver.quit()
    
    return uniNum

#findUni("nara")