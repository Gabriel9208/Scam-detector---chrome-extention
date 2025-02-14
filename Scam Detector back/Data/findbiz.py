import requests, json, re
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import os
import logging

from urllib.parse import urlparse


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
                # 中文越長越好 英文次數出現越多越長越好 中文優先
                if all_chinese_chars(substr) and count > substring[1]:
                    substring = (substr, count, True)
                elif all_chinese_chars(substr) and count == substring[1] and len(substr) > len(substring[0]):
                    substring = (substr, count, True)
                elif not substring[2] and not all_chinese_chars(substr) and count > substring[1]:
                    substring = (substr, count, False)
                elif not substring[2] and not all_chinese_chars(substr) and len(substr) > len(substring[0]):
                    substring = (substr, count, False)
    return substring

def filterCompanyName(companyName:str):
    if re.search(r'[\u4e00-\u9fff]', companyName):
        companyName = re.sub(r'[^\u4e00-\u9fff ]', '', companyName)
    return companyName
    
def findUniNum(domain:str, companyName:str=None):
    """
    Find the unified business number (統一編號) for a company using domain name and/or company name.

    Args:
        domain (str): The domain name to search for
        companyName (str, optional): The company name if known. Defaults to None.

    Returns:
        int: The unified business number if found, -1 if not found

    The function uses Google Custom Search API to:
    1. If company name provided:
        - Search directly for the company name on 台灣公司網
        - Extract unified number from search results
    2. If only domain provided:
        - Search for websites related to the domain
        - Extract common substrings from website titles
        - Use best substring to search 台灣公司網
        - Extract unified number from search results

    The function handles API quota limits and various error cases, returning -1 if no valid number found.
    """
    load_dotenv()
    
    uniNum = -1
    
    # Custom Search JSON API
    engine_api = os.getenv('search_engine_api_key')
    search_whole_net = os.getenv('find_num_search_id')
    search_num_id = os.getenv('find_company_search_id')
    
    if companyName:
        companyName = filterCompanyName(companyName)
        logging.info(f"decoded companyName: {companyName}")
        # reliable company name (from whois data or tls cert data)
        searchByCompanyName = f"https://www.googleapis.com/customsearch/v1?q={companyName}&key={engine_api}&cx={search_num_id}"
        
        try:
            searchDataWithCompanyName = json.loads(requests.get(searchByCompanyName, headers=headers).text)
            logging.info(f"Search response: {searchDataWithCompanyName}")
        except Exception as e:
            logging.error("findbiz limit", e)
            return findUniNum(domain)

        # have quota limit
        if 'items' not in searchDataWithCompanyName:
            logging.info(f"No search results found for company name: {companyName}")
            logging.info(f"Search response: {searchDataWithCompanyName}")
            logging.info(f"domain: {(domain)}")
            return findUniNum(domain)  
        
        if len(searchDataWithCompanyName["items"]) < 1:
            logging.info(f"No items found in search results for company name: {companyName}")
            return findUniNum(domain)
        
        companyNameUrl = searchDataWithCompanyName["items"][0].get("formattedUrl", "")
        logging.info(f"First company URL: {companyNameUrl}")
        parsed_query = parse_qs(urlparse(companyNameUrl).query)
        
        # only search for one additional website if no is not in the url
        if "no" in parsed_query:
            uniNum = parsed_query["no"][0]
        else:
            uniNum = companyNameUrl[-8:-1]
                    
        logging.info(f"Returning unified number: {uniNum}")
        return uniNum
        
    try:
        # search based on domain only is not accurate
        # find the most relevant website related to the domain
        # use the title of the website as the company name
        # both domain and company name are not reliable though
        logging.info(f"Searching for uniNum with domain: {domain}")
        logging.info(f"Searching for website related to domain: {domain}")
        searchWebsiteRelatedToDomain = f"https://www.googleapis.com/customsearch/v1?q={domain}&key={engine_api}&cx={search_whole_net}"
        searchResult = json.loads(requests.get(searchWebsiteRelatedToDomain,headers=headers).text).get("items", [])
        
        if searchResult == []:
            logging.warning(f"No search results found for domain: {domain}")
            return -1
        
        websiteTitle = []
        for index, item in enumerate(searchResult):
            if index >= 10:
                break
            websiteTitle.append(item["title"])
        
        logging.info(f"Extracted website titles: {websiteTitle}")
        query = long_substr(websiteTitle)
        
        # if title doesn't exist enough time, use the domain to query
        if isinstance(query, tuple) and query[1] <= 2:
            logging.info("Using domain as query due to insufficient common substring")
            query = domain
        elif isinstance(query, tuple):
            logging.info(f"Using common substring as query: {query[0]}")
            query = query[0]
        else:
            logging.warning("Unexpected result from long_substr, using domain as fallback")
            query = domain  # Fallback in case long_substr returns unexpected type

        logging.info(f"Final query for company search: {query}")
        # Utilize 台灣公司網 to get uninum -> 利用公司名稱以及域名來搜尋
        searchWithCompanyName = f"https://www.googleapis.com/customsearch/v1?q={query}&key={engine_api}&cx={search_num_id}"

        # query 台灣公司網 for result, and extract the num at the end of 台灣公司網 url
        searchDataWithCompanyName = json.loads(requests.get(searchWithCompanyName, headers=headers).text)
        try: 
            if "items" in searchDataWithCompanyName:
                nameUrl = searchDataWithCompanyName["items"][0]["formattedUrl"] 
                logging.info(f"Found company URL: {nameUrl}")
                uniNum = parse_qs(urlparse(nameUrl).query)["no"][0]
                logging.info(f"Extracted unified number: {uniNum}")
        except (IndexError, KeyError) as e:
            try:
                # If "no" parameter not found, try getting from the second search result
                nameUrl = searchDataWithCompanyName["items"][1]["formattedUrl"]
                uniNum = parse_qs(urlparse(nameUrl).query)["no"][0]
                logging.info(f"Extracted unified number from second result: {uniNum}")
            except (KeyError, IndexError) as e:
                logging.error(f"Failed to extract unified number: {e}")
                uniNum = -1
        
        return uniNum
                
    except Exception as e:
        return -1
    
        
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
        print('At line 170: ConnectionError: ', e)
        return {}
    except json.JSONDecodeError as e:
        print(f'At line 172: JSONDecodeError: {e}')
        return {}
    except Exception as e:
        print(f'At line 174: Unhandled Exception: {e}')
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
    domain = urlparse(url).netloc

    if num:
         # If a business number is provided, directly request business info
         return request_to_biz(num)[0]
     
    logging.info(f"findbiz companyName: {companyName}")
    if companyName:        
        uniNum = findUniNum(domain, companyName)
        if request_to_biz(uniNum):
            result = request_to_biz(uniNum)[0]
            return result
        else:
            return {}
    
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
        print("At line 252: ValueError:", e)
        return {}
    except Exception as e: 
        # Handle any other exceptions
        print('At line 183: Other exception:', e)    
        return {}



if __name__ == "__main__":
    print(findbiz("https://www.esunbank.com/zh-tw/personalc")) 