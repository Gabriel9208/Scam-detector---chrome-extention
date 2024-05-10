import requests, json
from findUniNum import findUni

def findbiz(url:str):
    name = url.split('/')[2].split('.')[::-1]
    noUse = ['tw', 'org', 'com', 'net', 'edu', 'gov', 'mil', ".aero", ".biz", ".coop", ".info", ".museum", ".name", ".pro", "moe"]
    for n in name:
        if n not in noUse:
            name = n
            break
         
    try:
        uniNum = findUni(name)
    except ValueError as e: 
        print("ValueError:", e)
    except Exception as e: 
        print('Other exception:', e)
        
        
    apis = [f"https://data.gcis.nat.gov.tw/od/data/api/5F64D864-61CB-4D0D-8AD9-492047CC1EA6?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50", # 公司登記基本資料-應用一
           f"https://data.gcis.nat.gov.tw/od/data/api/F05D1060-7D57-4763-BDCE-0DAF5975AFE0?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50", # 公司登記基本資料-應用二
           f"https://data.gcis.nat.gov.tw/od/data/api/236EE382-4942-41A9-BD03-CA0709025E7C?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50"] # 公司登記基本資料-應用三
    try:
        for url in apis:
            r = requests.get(url)
            if r.text != '':
                content = json.loads(r.text)
                #print(content)
                return content
                #break
    except requests.exceptions.ConnectionError as e:
        print('ConnectionError: ', e)
        return {}
    except json.JSONDecodeError as e:
        print(f'JSONDecodeError: {e}')
        return {}
    except Exception as e:
        print(f'Unhandled Exception: {e}')
        return {}

# Just for testing
# test = input("url: ")
#test = "https://www.nvidia.com/zh-tw/"
#findbiz(test)