import re
from sys import exit
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def findUni(coName:str):
    uniNum = ""

    # Don't show the window
    firefoxOpt = Options()
    firefoxOpt.add_argument("-headless")

    '''options=firefoxOpt'''
    driver = webdriver.Firefox(options=firefoxOpt)
    driver.implicitly_wait(5)
    try:
        driver.get('https://www.google.com/')
        searchBar = driver.find_element(By.NAME, "q")
        searchBar.send_keys(f"{coName} 公司統編")
        searchBar.send_keys(Keys.ENTER)
        
        # get link
        links = driver.find_elements(By.CLASS_NAME, 'yuRUbf')
        
        # get 
        driver.get(links[0].find_element(By.TAG_NAME, 'a').get_attribute('href'))
        html = driver.page_source
        # print(html)
        match = re.findall(r'統編(?:<\/b> :<\/td> <td colspan="2">|.*)\d{8}', html)
        driver.close()
        try:
            uniNum = match[0][-8:]
            return uniNum
        except Exception as e:
            print(e)
            exit(0)
                
    except Exception as e:
        driver.close()
        print(e)
        exit(0)