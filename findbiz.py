import requests, json
import findUniNum as uni

url = input("URL: ")
name = url.split('/')[2].split('.')[-2]
uniNum = uni.findUni(name)
url = f"https://data.gcis.nat.gov.tw/od/data/api/5F64D864-61CB-4D0D-8AD9-492047CC1EA6?$format=json&$filter=Business_Accounting_NO eq {uniNum}&$skip=0&$top=50"
r = requests.get(url)
content = json.loads(r.text)
print(content)