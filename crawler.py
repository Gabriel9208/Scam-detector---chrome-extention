from selenium import webdriver

def crawl(url:str):
    driver = webdriver.Firefox()
    driver.get(url)
    content = driver.page_source
    driver.quit()
    print(content)
    
crawl(input("URL: "))