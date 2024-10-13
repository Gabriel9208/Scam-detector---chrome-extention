import requests, json, re
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import os
import logging

from Data.whoisInfo import urlToDomain


headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd'
        }

def contains_invalid_chars(s):
    # This pattern matches any character that is not a-zA-Z, space, or Chinese
    pattern = r'[^0-9a-zA-Z\s\u4e00-\u9fff]'
    
    # If we find any match, the string contains invalid characters
    return bool(re.search(pattern, s))

def all_chinese_chars(s):
    # This pattern matches any character that is not a-zA-Z, space, or Chinese
    pattern = r'[^0-9\s\u4e00-\u9fff]'
    
    # If we find any match, the string contains invalid characters
    return not bool(re.search(pattern, s))
        
def long_substr(data):
    IS_CHINESE = False
    substring = ('', 0, IS_CHINESE)
    
    if not data:
        return ''
    
    for main in data:
        if not main:
            return ''
        
        # Generate all substrings of the first string
        substrings = [main[i:j] for i in range(len(main)) for j in range(i + 1, len(main) + 1)]
        
        # Sort substrings by length, descending
        substrings = substrings[::-1]
        required_count = 2
        
        for substr in substrings:
            if len(substr) < 3:  # Ignore very short substrings
                continue
            count = sum(1 for s in data if substr in s)
            if count >= required_count and not contains_invalid_chars(substr) :
                # 中文越長越好 英文次數出現越多越好 中文優先
                if all_chinese_chars(substr) and len(substr) > len(substring[0]):
                    substring = (substr, count, True)
                elif not substring[2] and not all_chinese_chars(substr) and count > substring[1]:
                    substring = (substr, count, False)
        
    return substring

def findUniNum(domain:str, companyName:str=None):
    load_dotenv()
    
    # Custom Search JSON API
    engine_api = os.getenv('search_engine_api_key')
    search_id = "53af66ed5b0174cc7"
    search_num_id = "80750484c968f42c8"
    
    if companyName:
        companyName = re.sub(r'[^a-zA-Z\s.\u4e00-\u9fff]+', '', companyName)
        # reliable company name (from whois data or tls cert data)
        searchByCompanyName = f"https://www.googleapis.com/customsearch/v1?q={companyName}&key={engine_api}&cx={search_num_id}"
        
        try:
            logging.info(f"Searching for uniNum with companyName: {companyName}")
            searchDataWithCompanyName = json.loads(requests.get(searchByCompanyName,headers=headers).text)
            logging.info(f"Search response: {searchDataWithCompanyName}")
        except Exception as e:
            logging.error("findbiz limit", e)
            return -1

        # have quota limit
        if 'items' not in searchDataWithCompanyName:
            logging.info(f"No search results found for company name: {companyName}")
            logging.debug(f"Search response: {searchDataWithCompanyName}")
            return findUniNum(domain)
            
        companyNameUrl = searchDataWithCompanyName["items"][0]["formattedUrl"]
        logging.info(f"First company URL: {companyNameUrl}")
        parsed_query = parse_qs(urlparse(companyNameUrl).query)
        
        # only search for one additional website if no is not in the url
        if "no" in parsed_query:
            uniNum = parsed_query["no"][0]
            logging.info(f"Unified number found in first URL: {uniNum}")
        else:
            logging.info("No unified number in first URL, checking second URL")
            companyNameUrl = searchDataWithCompanyName["items"][1]["formattedUrl"]
            logging.info(f"Second company URL: {companyNameUrl}")
            parsed_query = parse_qs(urlparse(companyNameUrl).query)
            if "no" in parsed_query:
                uniNum = parsed_query["no"][0]
                logging.info(f"Unified number found in second URL: {uniNum}")
            else:
                uniNum = -1
                logging.warning("No unified number found in either URL")
                
        logging.info(f"Returning unified number: {uniNum}")
        return uniNum
        
    try:
        # search based on domain only is not accurate
        # find the most relevant website related to the domain
        # use the title of the website as the company name
        # both domain and company name are not reliable though
        searchWebsiteRelatedToDomain = f"https://www.googleapis.com/customsearch/v1?q={domain}&key={engine_api}&cx={search_id}"
        searchResult = json.loads(requests.get(searchWebsiteRelatedToDomain,headers=headers).text)["items"]
        
        websiteTitle = []
        for index, item in enumerate(searchResult):
            if index >= 10:
                break
            websiteTitle.append(item["title"])
        
        query = long_substr(websiteTitle)
        
        # if tiltle doesn't exist enough time, use the domain to query
        if query[1] <= 2:
            query = domain
        else :
            query = query[0]

        # Utilize 台灣公司網 to get uninum -> 利用公司名稱以及域名來搜尋
        searchWithCompanyName = f"https://www.googleapis.com/customsearch/v1?q={query}&key={engine_api}&cx={search_num_id}"

        # query 台灣公司網 for result, and extract the num at the end of 台灣公司網 url
        searchDataWithCompanyName = json.loads(requests.get(searchWithCompanyName,headers=headers).text)
        try: 
            nameUrl = searchDataWithCompanyName["items"][0]["formattedUrl"] 
        except:
           uniNum = -1
                  
        uniNum = parse_qs(urlparse(nameUrl).query)["no"][0]
        
        return uniNum
                
    except Exception as e:
        print(e)
    
    return uniNum
        
def request_to_biz(uniNum):
    if uniNum == -1:
        return {}
    
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
    
def findbiz(url:str, companyName:str=None, num=None):
    '''
    Use domain to find the uniNum, then use uniNum to find the biz info

    Args:
        domain (str): The domain name to search for business information
        num (str, optional): The business registration number, if known. Defaults to None.

    Returns:
        dict: A dictionary containing business information, or an empty dict if not found
    '''
    domain = urlToDomain(url)
    if num:
         # If a business number is provided, directly request business info
         return request_to_biz(num)[0]
     
    logging.info(f"findbiz companyName: {companyName}")
    if companyName:
        logging.info(f"Searching for uniNum with domain: {domain} and companyName: {companyName}")
        uniNum = findUniNum(domain, companyName)
        logging.info(f"Found uniNum: {uniNum}")
        result = request_to_biz(uniNum)[0]
        logging.info(f"Business info result: {result}")
        return result
    
    try:       
        logging.info(f"Searching for uniNum with domain: {domain}")
        uniNum = findUniNum(domain)
        logging.info(f"Found uniNum: {uniNum}")
        # Request and return business info using the found number 
        result = request_to_biz(uniNum)[0]
        logging.info(f"Business info result: {result}")
        return result
    except ValueError as e: 
        # Handle specific ValueError exceptions
        print("ValueError:", e)
        return {}
    except Exception as e: 
        # Handle any other exceptions
        print('Other exception:', e)    
        return {}
    except Exception as e:
        # Catch any unexpected exceptions
        print(e)
        return {}

# print(findbiz("momoshop.com.tw")) # momo 
# print(findbiz("gvm.com.tw/")) # 遠見雜誌 
# print(findbiz("cht.com.tw")) # 中華電信
# print(findbiz("bnext.com.tw")) # 數位時代
# print(findbiz("nccc.com.tw")) # 財團法人聯合信用卡處理中心全球資訊網 
# print(findbiz("104.com.tw")) # 104 
# print(findbiz("591.com.tw")) # 591
# print(findbiz("1111.com.tw")) # 1111
# print(findbiz("www.esunbank.com")) # 1111

#print(findbiz("https://www.104.com.tw/"))

if __name__ == "__main__":
    print(findbiz("https://www.dbs.com.tw/personal-zh/default.page", "DBS Bank Ltd"))