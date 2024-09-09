import requests, json, re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from difflib import SequenceMatcher


headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd'
        }

def findUniNum(companyName:str, domain:str):
    if not companyName:
        raise ValueError("Company name cannot be empty. Maybe error parsing the url.")
    
    # Custom Search JSON API key: AIzaSyAfmXutFEOZMqhDzQpoCWfXL1ivLD90Jqs
    try:
        load_dotenv()
        # Custom Search JSON API
        engine_api = os.getenv('search_engine_api_key')
        search_engine_id = "80750484c968f42c8"
        
        # Utilize 台灣公司網 to get uninum -> 利用公司名稱以及域名來搜尋
        searchWithDomain = f"https://www.googleapis.com/customsearch/v1?q={domain}&key={engine_api}&cx={search_engine_id}"
        searchWithCompanyName = f"https://www.googleapis.com/customsearch/v1?q={companyName}&key={engine_api}&cx={search_engine_id}"

        # query 台灣公司網 for result, and extract the num at the end of 台灣公司網 url
        searchDataWithDomain = json.loads(requests.get(searchWithDomain,headers=headers).text)   
        try:    
            domainUrl = searchDataWithDomain["items"][0]["formattedUrl"] 
            domainTitle = searchDataWithDomain["items"][0]["title"] 
            domainTitleMatchRatio = SequenceMatcher(None, domainTitle, companyName).ratio()

        except:
            domainTitleMatchRatio = 0
        
        searchDataWithCompanyName = json.loads(requests.get(searchWithCompanyName,headers=headers).text)
        try: 
            nameUrl = searchDataWithCompanyName["items"][0]["formattedUrl"] 
            nameTitle = searchDataWithCompanyName["items"][0]["title"] 
            nameTitleMatchRatio = SequenceMatcher(None, nameTitle, companyName).ratio()

        except:
            nameTitleMatchRatio = 0
       
        uniNum = None
        
        # Title compare
        if domainTitleMatchRatio > nameTitleMatchRatio:
            uniNum = parse_qs(urlparse(domainUrl).query)["no"][0]
        elif domainTitleMatchRatio < nameTitleMatchRatio:
            uniNum = parse_qs(urlparse(nameUrl).query)["no"][0]
        elif domainTitleMatchRatio == 0:
            uniNum = -1
        
        return uniNum
                
    except Exception as e:
        print(e)
    
    return uniNum
        
def request_to_biz(uniNum):
    apis = [f"https://data.gcis.nat.gov.tw/od/data/api/5F64D864-61CB-4D0D-8AD9-492047CC1EA6?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50", # 公司登記基本資料-應用一
           f"https://data.gcis.nat.gov.tw/od/data/api/F05D1060-7D57-4763-BDCE-0DAF5975AFE0?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50", # 公司登記基本資料-應用二
           f"https://data.gcis.nat.gov.tw/od/data/api/236EE382-4942-41A9-BD03-CA0709025E7C?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50"] # 公司登記基本資料-應用三
    
    try:
        for url in apis:
            r = requests.get(url)
            
            if r.text != '':
                content = json.loads(r.text)
                return content
            
    except requests.exceptions.ConnectionError as e:
        print('ConnectionError: ', e)
        return {}
    except json.JSONDecodeError as e:
        print(f'JSONDecodeError: {e}')
        return {}
    except Exception as e:
        print(f'Unhandled Exception: {e}')
        return {}
    
def findbiz(url:str, num=None):
    if num:
         return request_to_biz(num)
    try:        
        # get title of the page
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        title_text = soup.title.string
        
        # split by Chinese characters, English characters and numbers
        companyName = re.split(r'([^\u4e00-\u9fffa-zA-Z0-9 |]+)', title_text)[0]

        try:
            uniNum = findUniNum(companyName, urlparse(url).netloc)
            return request_to_biz(uniNum)[0]
        
        except ValueError as e: 
            print("ValueError:", e)
            return {}
        except Exception as e: 
            print('Other exception:', e)
            return {}
    except Exception as e:
        print(e)
        return {}

# print(findbiz("https://www.momoshop.com.tw/main/Main.jsp")) # momo 
# print(findbiz("https://www.gvm.com.tw/")) # 遠見雜誌 
# print(findbiz("https://www.cht.com.tw/home/consumer")) # 中華電信
# print(findbiz("https://www.bnext.com.tw/")) # 數位時代
# print(findbiz("https://www.nccc.com.tw/wps/wcm/connect/zh/home")) # 財團法人聯合信用卡處理中心全球資訊網 
# print(findbiz("https://www.104.com.tw/jobs/main/")) # 104 
# print(findbiz("https://www.591.com.tw/")) # 591


