import requests
import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time
import datetime
from dateutil import parser

def calculate_days_difference(date1, date2):
    """
    Calculate days difference between two dates
    Returns -1 if date1 > date2 (expired)
    """
    if date1 > date2:
        return -1
    diff_time = abs(date2 - date1)
    return diff_time.days

def parse_date(date_string):
    """
    Parse date string to datetime object
    Returns None if parsing fails
    """
    if not date_string or not isinstance(date_string, str):
        return None

    try:
        # Try different date formats
        formats = [
            "%Y-%m-%d %H:%M:%S (UTC+8)",  # 2029-07-12 00:00:00 (UTC+8)
            "%Y-%m-%dT%H:%M:%SZ",         # 2025-04-21T04:00:00Z
            "%Y-%m-%dT%H:%M:%S",          # 2025-04-04T07:55:39
            "%b %d %H:%M:%S %Y GMT"       # Mar 3 23:59:59 2025 GMT
        ]

        for fmt in formats:
            try:
                date = datetime.datetime.strptime(date_string, fmt)
                # Convert to UTC+8
                return date.replace(tzinfo=datetime.timezone.utc).astimezone(
                    datetime.timezone(datetime.timedelta(hours=8))
                )
            except ValueError:
                continue

        # If none of the formats match, try parsing with dateutil
        return parser.parse(date_string).astimezone(
            datetime.timezone(datetime.timedelta(
                hours=8
            ))
        )
    except ValueError:
        return None

def analyze_url(url):
    base_url = "http://localhost:8000/scam-detector/detail"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {"url": url}
    
    # Initialize score contributions as defined in the frontend
    score_contributions = {
        "domainExpired": 2,
        "tlsExpired": 2,
        "inPhishDB": 10,
        "isDomainExpiringSoon": 0.5,
        "isTLSExpiringSoon": 0.5,
        "caStatus": 1,
        "isDomainNew": 0.5,
        "businessInfo": 1,
        "pageInfo": 0.5,
        "tlsInfo": 1,
        "whoisInfo": 1
    }

    try:
        # Initialize score breakdown dictionary
        score_breakdown = {
            "domainExpired": 0,
            "tlsExpired": 0,
            "inPhishDB": 0,
            "isDomainExpiringSoon": 0,
            "isTLSExpiringSoon": 0,
            "caStatus": 0,
            "isDomainNew": 0,
            "businessInfo": 0,
            "pageInfo": 0,
            "tlsInfo": 0,
            "whoisInfo": 0
        }
        
        # Fetch all required data
        whois_info = requests.post(f"{base_url}/whois/", json=data).json()
        tls_info = requests.post(f"{base_url}/tls/", json=data).json()
        page_info = requests.post(f"{base_url}/web-content/", json=data).json()
        phish_info = requests.post("http://localhost:8000/scam-detector/analysis/phish/", json=data).json()
        
        # Determine organization name from whois_info
        org_name = ""
        org_name_hidden = ["encrypt", "protected", "disclosed", "Redacted", "privacy"]
        
        print(whois_info)
        if "Registrant" in whois_info:
            registrant = re.match(r'^[a-zA-Z\u4e00-\u9fff\s0-9]+', whois_info["Registrant"])[0] if re.match(r'^[a-zA-Z\u4e00-\u9fff\s0-9]+', whois_info["Registrant"]) else ""
            if not any(keyword.lower() in registrant.lower() for keyword in org_name_hidden):
                org_name = registrant
        elif "Registrant Organization" in whois_info:
            registrant_org = whois_info["Registrant Organization"]
            if not any(keyword.lower() in registrant_org.lower() for keyword in org_name_hidden):
                org_name = registrant_org

        # Fetch business info with or without organization name
        if org_name:
            business_info = requests.post(f"{base_url}/findbiz/", json={"url": url, "organizationName": org_name}).json()
        else:
            business_info = requests.post(f"{base_url}/findbiz/", json=data).json()
        
        # Additional check for CA status
        ca_info = None
        if tls_info and "issuer" in tls_info:
            ca_name = tls_info["issuer"].get("Common Name") or tls_info["issuer"].get("commonName")
            ca_request = {"ca": ca_name}
            ca_response = requests.post("http://localhost:8000/scam-detector/analysis/ca/", json=ca_request).json()
            ca_info = ca_response.get("result", None)

        # Calculate current date in UTC+8
        current_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        
        # Initialize expiration flags
        domain_expired = False
        domain_expiring_soon = False
        tls_expired = False
        tls_expiring_soon = False
        is_domain_new = False

        # Check domain dates if whois info is available
        if whois_info and "expiration_date" in whois_info:
            expiration_date = parse_date(whois_info["expiration_date"])
            if expiration_date:
                days_until_expiration = calculate_days_difference(current_date, expiration_date)
                domain_expired = days_until_expiration == -1
                domain_expiring_soon = 0 <= days_until_expiration <= 30

            # Check if domain is new
            if "creation_date" in whois_info:
                creation_date = parse_date(whois_info["creation_date"])
                if creation_date:
                    domain_age = calculate_days_difference(creation_date, current_date)
                    is_domain_new = domain_age != -1 and domain_age <= 365

        # Check TLS certificate dates
        if tls_info and "notAfter" in tls_info:
            tls_expiration_date = parse_date(tls_info["notAfter"])
            if tls_expiration_date:
                days_until_tls_expiration = calculate_days_difference(current_date, tls_expiration_date)
                tls_expired = days_until_tls_expiration == -1
                tls_expiring_soon = 0 <= days_until_tls_expiration <= 30

        # Calculate risk score with breakdown tracking
        risk_score = 0
        
        # Add score for domain expiration
        if domain_expired:
            score_breakdown["domainExpired"] = score_contributions["domainExpired"]
            risk_score += score_breakdown["domainExpired"]
        if domain_expiring_soon:
            score_breakdown["isDomainExpiringSoon"] = score_contributions["isDomainExpiringSoon"]
            risk_score += score_breakdown["isDomainExpiringSoon"]
        
        # Add score for TLS expiration
        if tls_expired:
            score_breakdown["tlsExpired"] = score_contributions["tlsExpired"]
            risk_score += score_breakdown["tlsExpired"]
        if tls_expiring_soon:
            score_breakdown["isTLSExpiringSoon"] = score_contributions["isTLSExpiringSoon"]
            risk_score += score_breakdown["isTLSExpiringSoon"]
            
        # Add score for new domain
        if is_domain_new:
            score_breakdown["isDomainNew"] = score_contributions["isDomainNew"]
            risk_score += score_breakdown["isDomainNew"]

        # Add score for phish database
        if phish_info.get("result", {}).get("in_phish_db", False):
            score_breakdown["inPhishDB"] = score_contributions["inPhishDB"]
            risk_score += score_breakdown["inPhishDB"]

        # Add score for missing or error information
        if not business_info or "error" in business_info or "detail" in business_info:
            score_breakdown["businessInfo"] = score_contributions["businessInfo"]
            risk_score += score_breakdown["businessInfo"]
        if not page_info or "error" in page_info or "detail" in page_info:
            score_breakdown["pageInfo"] = score_contributions["pageInfo"]
            risk_score += score_breakdown["pageInfo"]
        if not tls_info or "error" in tls_info or "detail" in tls_info:
            score_breakdown["tlsInfo"] = score_contributions["tlsInfo"]
            risk_score += score_breakdown["tlsInfo"]
        if not whois_info or "error" in whois_info or "detail" in whois_info:
            score_breakdown["whoisInfo"] = score_contributions["whoisInfo"]
            risk_score += score_breakdown["whoisInfo"]

        return {
            "url": url,
            "risk_score": risk_score,
            "status": "success",
            "score_breakdown": score_breakdown,
            "details": {
                "whois": whois_info if whois_info else None,
                "tls": tls_info if tls_info else None,
                "business": business_info if business_info else None,
                "page": page_info if page_info else None,
                "in_phish_db": phish_info.get("result", {}).get("in_phish_db", False),
                "ca_status": ca_info
            }
        }

    except Exception as e:
        return {
            "url": url,
            "risk_score": -1,
            "status": "error",
            "error_message": str(e),
            "score_breakdown": {k: 0 for k in score_contributions.keys()}
        }

def batch_analyze_urls(urls, max_workers=3):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create futures with delays between submissions
        futures = []
        for url in urls:
            futures.append(executor.submit(analyze_url, url))
            time.sleep(10)  # Add 1 second delay between submissions
            
        for future in futures:
            try:
                result = future.result()
                results.append(result)
                print(f"Analyzed {result['url']}: Score = {result['risk_score']}")
            except Exception as e:
                print(f"Error processing URL: {e}")
    
    return results 

# Example usage
if __name__ == "__main__":
    # List of URLs to test
    urls_to_test = [
        "https://www.hncb.com.tw/wps/portal/HNCB/"  ]
    
    results = batch_analyze_urls(urls_to_test)
    
    # Convert results to DataFrame with score breakdown
    df = pd.DataFrame([
        {
            'url': r['url'],
            'total_risk_score': r['risk_score'],
            'status': r['status'],
            **r.get('score_breakdown', {})  # Unpack score breakdown into columns
        }
        for r in results
    ])
    
    print("\nResults Summary:")
    print(df)
    
    # Save to CSV with all columns
    df.to_csv("url_analysis_results.csv", index=False)
    
    