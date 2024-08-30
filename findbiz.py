import requests, json
from urllib.parse import urlparse, parse_qs

def findUni(companyName:str):
    if not companyName:
        raise ValueError("Company name cannot be empty. Maybe error parsing the url.")
    
    uniNum = ""
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
    
    name = urlparse(url).netloc.split('.')[::-1]
    noUse = ['tw', 'org', 'com', 'net', 'edu', 'gov', 'mil', "aero", "biz", "coop", "info", "museum", "name", "pro", "moe", "me"]
    
    for n in name:
        if n not in noUse:
            name = n
            break
    
    try:
        uniNum = findUni(name)
        return request_to_biz(uniNum)
    
    except ValueError as e: 
        print("ValueError:", e)
        return {}
    except Exception as e: 
        print('Other exception:', e)
        return {}


'''
start = time.time()
print(findbiz("https://www.momoshop.com.tw/main/Main.jsp"))
stop = time.time()
print((stop-start) * 10 * 10 * 10)
'''
print(findbiz("https://www.esunbank.com/zh-tw/personal"))