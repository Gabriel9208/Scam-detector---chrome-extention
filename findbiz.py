import requests, json, re
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


def findUniNum(companyName:str):
    if not companyName:
        raise ValueError("Company name cannot be empty. Maybe error parsing the url.")
    
    # Custom Search JSON API key: AIzaSyAfmXutFEOZMqhDzQpoCWfXL1ivLD90Jqs
    try:
        # Custom Search JSON API
        search_engine_api_key = "AIzaSyAfmXutFEOZMqhDzQpoCWfXL1ivLD90Jqs"
        search_engine_id = "80750484c968f42c8"
        query = f"{companyName} 公司統編"
        
        searchUrl = f"https://www.googleapis.com/customsearch/v1?q={query}&key={search_engine_api_key}&cx={search_engine_id}"
        searchData = json.loads(requests.get(searchUrl).text)        

        urlIncludeNum = searchData["items"][0]["formattedUrl"]
        uniNum = parse_qs(urlparse(urlIncludeNum).query)["no"][0]
        
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://google.com',
        }
        
        # get title of the page
        page = requests.get(url, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        title_text = soup.title.string
        
        # split by Chinese characters, English characters and numbers
        companyName = re.split(r'([^\u4e00-\u9fffa-zA-Z0-9]+)', title_text)[0]

        try:
            uniNum = findUniNum(companyName)
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


