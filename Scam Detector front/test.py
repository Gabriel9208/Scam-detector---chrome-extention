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
    Args:
        date1: First date (usually creation date)
        date2: Second date (usually current date)
    Returns:
        int: Number of days between dates
             -1 if invalid comparison
    """
    try:
        # Ensure both dates have timezone info
        if date1.tzinfo is None:
            date1 = date1.replace(tzinfo=datetime.timezone.utc)
        if date2.tzinfo is None:
            date2 = date2.replace(tzinfo=datetime.timezone.utc)
            
        # Calculate the actual difference without abs()
        diff_time = date2 - date1
        return diff_time.days
    except Exception:
        return -1

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
            "%Y-%m-%dt%H:%M:%Sz",         # lowercase variant
            "%Y-%m-%dT%H:%M:%S",          # 2025-04-04T07:55:39
            "%Y-%m-%dt%H:%M:%S",          # lowercase variant
            "%b %d %H:%M:%S %Y GMT",      # Mar 3 23:59:59 2025 GMT
            "%Y-%m-%d %H:%M:%S"           # 2024-03-25 00:11:03
        ]

        for fmt in formats:
            try:
                date = datetime.datetime.strptime(date_string, fmt)
                # Convert to UTC+8
                if fmt.endswith("GMT"):
                    # For GMT format, first convert to UTC
                    date = date.replace(tzinfo=datetime.timezone.utc)
                elif fmt.endswith("Z") or fmt.endswith("z"):
                    # For ISO format with Z, it's already UTC
                    date = date.replace(tzinfo=datetime.timezone.utc)
                elif fmt.endswith("(UTC+8)"):
                    # For UTC+8 format, strip the timezone part and treat as UTC+8
                    date = date.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
                else:
                    # For formats without timezone, assume UTC
                    date = date.replace(tzinfo=datetime.timezone.utc)
                
                # Return the raw datetime without timezone conversion
                return date
            except ValueError:
                continue

        # If none of the formats match, try parsing with dateutil
        # This is a fallback for other possible formats
        return parser.parse(date_string)
    except (ValueError, TypeError):
        return None

def get_domain_creation_date(whois_info):
    """Extract domain creation date from whois info with multiple field name checks"""
    if not whois_info:
        return None
        
    creation_date_fields = [
        "creation_date",
        "creationDate",
        "Record created",
        "Creation Date", 
        "Created Date",
        "Registration Time",
        "Creation Time"
    ]
    
    # Try each possible field name
    for field in creation_date_fields:
        if field in whois_info:
            date_str = whois_info[field]
            parsed_date = parse_date(date_str)
            if parsed_date:
                return parsed_date
    
    return None

def analyze_url(url):
    base_url = "http://localhost:8000/scam-detector/detail"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {"url": url}
    
    # Update score contributions to match frontend exactly
    score_contributions = {
        "domainExpired": 2,
        "tlsExpired": 2,
        "inPhishDB": 10,
        "isDomainExpiringSoon": 0.5,
        "isTLSExpiringSoon": 0.5,
        "caStatus": 2,
        "isDomainNew": 0.5,
        "businessInfo": 1,
        "pageInfo": 0.5,
        "tlsInfo": 1,
        "whoisInfo": 1,
        "fakeDomain": 1
    }

    try:
        # Initialize score breakdown dictionary
        score_breakdown = {k: 0 for k in score_contributions.keys()}
        
        # Fetch all required data
        whois_info = requests.post(f"{base_url}/whois/", json=data).json()
        tls_info = requests.post(f"{base_url}/tls/", json=data).json()
        page_info = requests.post(f"{base_url}/web-content/", json=data).json()
        phish_info = requests.post("http://localhost:8000/scam-detector/analysis/phish/", json=data).json()
        
        # Get page source for fake domain detection
        page_source = page_info.get("source", "") if page_info and isinstance(page_info, dict) else ""
        
        # Fetch fake domain result with page source
        fake_domain_data = {"url": url, "source": page_source}
        fake_domain_info = requests.post(f"{base_url}/fake-domain/", json=fake_domain_data).json()
        is_fake_domain = fake_domain_info.get("result", {}).get("result", False) if fake_domain_info else False
        
        # Determine organization name from whois_info
        org_name = ""
        org_name_hidden = ["encrypt", "protected", "disclosed", "Redacted", "privacy"]
        
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
            ca_info = ca_response.get("result", None).get("is_trusted_ca", None)

        # Calculate current date in UTC+8
        current_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        
        # Initialize expiration flags
        domain_expired = False
        domain_expiring_soon = False
        tls_expired = False
        tls_expiring_soon = False
        is_domain_new = False

        # Check domain dates if whois info is available
        if whois_info :
            exp = (whois_info.get("expirationDate") or 
                  whois_info.get("Registry Expiry Date") or
                  whois_info.get("Expiration Date") or 
                  whois_info.get("Registrar Registration Expiration Date") or
                  whois_info.get("Record expires") or
                  whois_info.get("Expiration Time"))
            
            expiration_date = parse_date(exp)
            if expiration_date:
                days_until_expiration = calculate_days_difference(current_date, expiration_date)
                domain_expired = True if days_until_expiration < 0 else False
                domain_expiring_soon = True if 0 <= days_until_expiration <= 30 else False

            # Check if domain is new
            creation_date = get_domain_creation_date(whois_info)
            print(creation_date)
            if creation_date:
                domain_age = calculate_days_difference(creation_date, current_date)
                print(domain_age)
                is_domain_new = domain_age >= 0 and domain_age <= 365
            else:
                # If we can't determine domain age, consider it suspicious
                is_domain_new = True

        # Check TLS certificate dates
        if tls_info and "notAfter" in tls_info:
            tls_expiration_date = parse_date(tls_info["notAfter"])
            if tls_expiration_date:
                days_until_tls_expiration = calculate_days_difference(current_date, tls_expiration_date)
                tls_expired = True if days_until_tls_expiration < 0 else False
                tls_expiring_soon = True if 0 <= days_until_tls_expiration and days_until_tls_expiration <= 30 else False

        # Calculate risk score with exact same logic as frontend
        if domain_expired:
            score_breakdown["domainExpired"] = score_contributions["domainExpired"]
        
        if tls_expired:
            score_breakdown["tlsExpired"] = score_contributions["tlsExpired"]
            
        if phish_info.get("result", {}).get("in_phish_db", False):
            score_breakdown["inPhishDB"] = score_contributions["inPhishDB"]
            
        if domain_expiring_soon:
            score_breakdown["isDomainExpiringSoon"] = score_contributions["isDomainExpiringSoon"]
            
        if tls_expiring_soon:
            score_breakdown["isTLSExpiringSoon"] = score_contributions["isTLSExpiringSoon"]
            
        # CA status logic matching frontend
        if ca_info is None:
            score_breakdown["caStatus"] = score_contributions["caStatus"] / 2
        elif not ca_info:
            score_breakdown["caStatus"] = score_contributions["caStatus"]
            
        if is_domain_new:
            score_breakdown["isDomainNew"] = score_contributions["isDomainNew"]
            
        # Missing or error information checks matching frontend
        if not business_info or "error" in business_info or "detail" in business_info or business_info == {}:
            score_breakdown["businessInfo"] = score_contributions["businessInfo"]
            
        if not page_info or "error" in page_info or "detail" in page_info or page_info == {}:
            score_breakdown["pageInfo"] = score_contributions["pageInfo"]
            
        if not tls_info or "error" in tls_info or "detail" in tls_info or tls_info == {}:
            score_breakdown["tlsInfo"] = score_contributions["tlsInfo"]
            
        if not whois_info or "error" in whois_info or "detail" in whois_info or whois_info == {} or "The queried object does not exist" in whois_info:
            score_breakdown["whoisInfo"] = score_contributions["whoisInfo"]

        # Add fake domain score
        if is_fake_domain:
            score_breakdown["fakeDomain"] = score_contributions["fakeDomain"]

        # Calculate total risk score
        risk_score = sum(score_breakdown.values())

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
                "ca_status": ca_info,
                "is_fake_domain": is_fake_domain
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
        r"http://www.szydh.com/",
r"https://fubon.netlify.app",
r"https://apkfab.com/zh/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85ya/com.mitake.wls",
r"https://napkforpc.com/apk/tw.com.wls.eManager/",
r"https://steprimo.com/android/us/app/com.wlf.x3mobile/android/",
r"https://napkforpc.com/apk/com.wlf.x3mobile/",
r"https://www.apkmonk.com/app/com.twse.twseapp/",
r"https://www.apkmonk.com/app/tw.com.mitake.twse/",
r"https://www.apkmonk.com/app/com.mitake.wls/",
r"https://www.apkmonk.com/app/com.wls/",
r"https://www.apkmonk.com/app/com.wlf.x3mobile/",
r"https://www.apkmonk.com/app/tw.com.wls.Corporate/",
r"https://www.apkmonk.com/app/com.wls.tv/",
r"https://napkforpc.com/apk/com.mitake.wls/",
r"https://napkforpc.com/apk/com.mitake.wls.pad/",
r"https://napkforpc.com/app/tw.com.mitake.ios.touchstock.wls/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85ya/",     
r"https://napkforpc.com/apk/tw.com.wls.Corporate/",
r"https://napkforpc.com/fr/apk/com.mitake.wls/",
r"https://napkforpc.com/es/apk/com.mitake.wls/",
r"https://napkforpc.com/id/apk/com.mitake.wls/",
r"https://napkforpc.com/fa/apk/com.mitake.wls/",
r"https://napkforpc.com/ru/apk/com.mitake.wls/",
r"https://napkforpc.com/ko/apk/com.mitake.wls/",
r"https://apktume.com/android/us/app/com.chb.ebank/",
r"https://apkcombo.com/tw/%E7%A7%81%E6%88%BF%E9%96%B1%E8%AE%80/tw.com.megafunds.mypdfcatcher/",
r"https://gov-invoice.en.aptoide.com/app",
r"https://jihsun-bank.cn.aptoide.com/app",
r"https://steprimo.com/android/us/app/tw.com.wls.eManager/%E7%90%86%E8%B2%A1e%E7%AE%A1%E5%AE%B6/",
r"https://www.facebook.com/profile.php?id=100064472481082&mibextid=ZbWKwL",
r"https://www.facebook.com/dryadc?mibextid=ZbWKwL",
r"https://www.facebook.com/profile.php?id=100063781668762&mibextid=ZbWKwL",
r"https://androidappsapk.co/detail-元富證券「行動達人5���/",
r"https://sameapk.com/元富證券「行動達人5」/",
r"https://www.androidwearcenter.com/androidwear/app/%E5%85%86%E8%B1%90%E8%AD%89%E5%88%B8-%E8%A1%8C%E5%8B%95VIP/3599",
r"https://apksos.com/app/com.js.online",
r"https://horecasprendimai.lt/we",
r"https://bodyconnectionshealthandwellness.ca/wp-admin/css/colors/modern/grey/",
r"https://play.google.com/store/apps/details?id=com.rsc",
r"https://apktada.com/app/tw.megabank.geb.m",
r"https://www.apkmonk.com/app/tw.com.wls.eManager/",
r"http://click.promote.weebly.com/ls/click?upn=ZqalrN-2Brv5CyC4i51w4yaw-2F8tM0-2FkooK9i99xj6dACVbETNWt2pA3oCAa5EVd4qbI0JH_MvMB1Hb4ULJMPshwOrzfDahTR7x85bm-2BK-2Bt8J-2FLDK6Bj8JidwqXP0Ou47sqPzCXUDMF45DM0PQYQ3glJeAsQXFn7M5kPqghHBouXqG647Zb-2FbCGCaHRgUJBzfakms4Wr0mEM-2Bxbyh7OjCYRYqPXf-2BzLL4E-2Fv5ghXhZkPrXfhOr9XjiT6lc2L6Q3h2K2OyjrxjYQHtG3ibw3DSraJGz5otsEfmBgKvPYQY1KKioIWoKmftrH41hQhI7tAE2LrOma4i9H-2BA95AloBnhreKl2-2BHD9Kr74Ti5kzHfGROxMD1bzSMx-2Fgqdg-2BIgY7IIntpqUaKfaoY-2BkXsIp03-2F9HUmXBXCeMWhfhPwV1AgutAHx9y-2B2hdi0cL0hFjVqSYbA8khovsXzNYt0TdU6E2Znge2nVpsO6B14Rxl1WkrSsuCvdlFGroeoEJaPon2PWTrdz-2F1JhT9MmpF1QD3BxeunV-2FaWDtyehUnAlP5VugLxggxs3tOPM-3D",
r"https://p.weebly.com/23150114/aef73f0dcb/nnn.PNG",
r"https://secure.ethicspoint.com/domain/media/en/gui/59283/index.html",
r"https://apkgk.com/com.megabank.mobilebank",
r"https://apkgk.com/tw.megabank.exchange.m",
r"https://apkgk.com/tw.megabank.geb.m",
r"https://apkgk.com/com.megabank.megaezgo",
r"https://apkgk.com/com.megabank.matm",
r"https://apktume.com/android/us/app/com.mega.pad/",
r"https://apk.center/com.megabank.matm.html",
r"https://apk.center/tw.megabank.exchange.m.html",
r"https://apk.center/com.esecure.android.megaotp.html",
r"https://apktada.com/app/tw.com.megabank.mobilebank.pre",
r"https://apk.support/app-zh_cn/com.mega.megafundsinvest",
r"https://apktada.com/app/com.megabank.mobilebank",
r"https://apktada.com/app/com.megabank.megaezgo",
r"https://apkgk.com/com.mitake.wls",
r"https://apkgk.com/tw.com.wls.eManager",
r"https://apktume.com/android/us/app/com.ktb.ebank.app/",
r"https://apktume.com/android/us/app/com.mitake.taifex.impl/",
r"https://apkgk.com/zh-TW/com.mitake.wls",
r"https://apkgk.com/zh-TW/tw.com.wls.eManager",
r"https://www.androidblip.com/android-apps/com.ktb.ebank.app.html",
r"https://www.androidblip.com/android-apps/com.mitake.taifex.impl.html",
r"https://www.androidblip.com/android-apps/tw.com.taifex.tftrade.html",
r"https://apksos.com/app/com.cathay.securities.mBroker",
r"https://ydjk808.top/index/login/login",
r"https://nbank.skbank.com",
r"https://apkmonk.com/app/com.mitake.ctyopen/",
r"https://k3k4.cc/",
r"http://chunghwa.postgov.tw-tracknumber.saldanarealty.com/",
r"https://democbdc.kodelab.io/#/users",
r"https://ac1.dcloud.net.cn/app/acs",
r"https://www.apkmonk.com/app/tw.com.megafunds.megafunds/",
r"https://steprimo.com/android/us/app/com.mega.megafundsinvest/兆豐投信/",
r"https://apktume.com/android/us/app/com.skbank.creditcard/",
r"https://www.appbrain.com/app/%E7%90%86%E8%B2%A1e%E7%AE%A1%E5%AE%B6/tw.com.wls.eManager",
r"https://www.appbrain.com/app/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls",
r"http://twsebet.vip",
r"https://apkgk.com/com.mega.pad",
r"https://napkforpc.com/apk/com.mega/",
r"https://com-taifex-tftrade.en.aptoide.com/app",
r"https://steprimo.com/android/us/app/com.ibfs.ismart/%E5%9C%8B%E7%A5%A8%E4%BB%BB%E6%88%91%E8%B4%8F/",
r"https://qi-jiao-suo-xu-ni-jiao-yi-suo.fr.softonic.com/android",
r"https://twsebat.net/#/",
r"https://apktume.com/android/us/app/com.yuanta.android.nexus.vn/",
r"https://tpoeong-24.mom/#/login",
r"https://yuantastock666.com/api/user/login",
r"https://yuantastock666.com/#/login",
r"https://www.appbrain.com/app/%E6%9C%9F%E4%BA%A4%E6%89%80%E8%99%9B%E6%93%AC%E4%BA%A4%E6%98%93%E6%89%80/tw.com.taifex.tftrade",
r"https://apk.support/app/com.mega.megafundsinvest",
r"https://secure1.rsc.com.tw/index_mt.asp",
r"https://apkpure.com/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls/download/7.31.2.1369.WLS1.2.1004",
r"https://appagg.com/android/finance/guo-piao-ren-wo-ying-38492264.html?hl=zh-tw",
r"https://fghjknm.top/home/login/login",
r"https://apkpure.net/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls/download",
r"https://li-cai-eguan-jia.en.softonic.com/android",
r"https://com-taifex-tftrade.bd.aptoide.com/app",
r"https://fb77a.com/app/home/index",
r"https://fb66x.com/app/home/index",
r"https://fb55m.com/app/home/index",
r"https://apps.apple.com/tw/app/ewinner-plus-%E6%8A%95%E8%B3%87%E5%8B%9D%E6%89%8B/id1354835789?uo=4",
r"http://o-point.net/",
r"https://apkpure.net/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls/download/7.26.2.1168.WLS2.2.737.WLS4",
r"https://103.100.208.3/",
r"http://ensarlargida.com/-/union/login.php",
r"https://qi-jiao-suo-xu-ni-jiao-yi-suo.softonic.cn/android",
r"https://apkpure.com/tw/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls/download",
r"https://com-tbb.in.aptoide.com",
r"https://nfcal.cfd",
r"https://esunbank.win-john.com",
r"https://ninewill.github.io/SKBank/",
r"https://tajk.xyz/index.php?m=User&a=login",
r"https://taanjr.xyz/index.php?m=User&a=login",
r"https://twanjr.xyz/index.php?m=User&a=login",
r"https://txjr.xyz/index.php?m=User&a=login",
r"https://make-hex-32332e3232342e3139342e313234-rr.1u.ms/index.php?m=User&a=login",
r"https://23.224.194.125/index.php?m=User&a=login",
r"https://qi-jiao-suo-xu-ni-jiao-yi-suo.en.softonic.com/android",
r"https://apkpure.com/de/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls",
r"https://li-cai-eguan-jia.fr.softonic.com/android",
r"https://www.twse66.com/index/login/login",
r"https://www.androidblip.com/android-apps/com.sus.html",
r"https://appadvice.com/app/e5-9c-8b-e7-a5-a8-e6-8e-8c-e4-b8-ad-e6-9c-9f/1460342538",
r"https://vsiyu.buzz",
r"https://missupermarket.com",
r"https://apps.apple.com/tw/app/%E9%9A%A8%E8%BA%ABe%E8%A1%8C%E5%8B%95/id6630372583",
r"http://superset.ffbl.edu.rs",
r"https://apk.support/app-af/com.tbb.mb.prod",
r"https://apkgk.com/com.tbb",
r"http://tai-wan-qi-yin-zheng-quan.softonic-id.com/android",
r"https://tai-wan-qi-yin-zheng-quan.softonic-id.com/android",
r"http://tai-wan-qi-yin-zheng-quan.softonic.com/android",
r"https://tai-wan-qi-yin-zheng-quan.softonic.com/android",
r"http://tai-wan-qi-yin-zheng-quan.softonic-ar.com/android",
r"https://tai-wan-qi-yin-zheng-quan.softonic-ar.com/android",
r"http://tai-wan-qi-yin-zheng-quan.en.softonic.com/android",
r"https://tai-wan-qi-yin-zheng-quan.en.softonic.com/android",
r"http://tai-wan-qi-yin-zheng-quan.fr.softonic.com/android",
r"https://tai-wan-qi-yin-zheng-quan.fr.softonic.com/android",
r"http://tai-wan-qi-yin-zheng-quan.it.softonic.com/android",
r"https://tai-wan-qi-yin-zheng-quan.it.softonic.com/android",
r"http://tai-wan-qi-yin-zheng-quan.softonic-th.com/android",
r"https://tai-wan-qi-yin-zheng-quan.softonic-th.com/android",
r"http://tai-wan-qi-yin-zheng-quan.de.softonic.com/android",
r"https://tai-wan-qi-yin-zheng-quan.de.softonic.com/android",
r"http://tai-wan-qi-yin-zheng-quan.softonic.com.br/android",
r"https://tai-wan-qi-yin-zheng-quan.softonic.com.br/android",
r"http://apkgk.com/com.tbb",
r"http://tai-wan-qi-yin-zheng-quan.softonic.cn/android",
r"https://tai-wan-qi-yin-zheng-quan.softonic.cn/android",
r"http://www.softonic-id.com/download/tai-wan-qi-yin-zheng-quan/android/post-download",
r"https://www.softonic-id.com/download/tai-wan-qi-yin-zheng-quan/android/post-download",
r"https://com-tbb.en.aptoide.com",
r"https://tx0905.cn",
r"https://192.253.225.155",
r"https://yd0905.cn/index.php?m=User&a=login",
r"https://ydqhdd.cc/auth/login",
r"https://ydqhdf.cc/auth/login",
r"https://ydqhdg.cc/auth/login",
r"https://www.yuanda11698.com/login",
r"https://www.yuanda16155.com/login",
r"https://www.yuanda16608.com/login",
r"https://www.yuanda19888.com/login",
r"https://www.yuanda50801.com/login",
r"https://www.yuanda55191.com/login",
r"https://www.yuanda60166.com/login",
r"https://www.yuanda60666.com/login",
r"https://www.yuanda66988.com/login",
r"https://www.yuanda71616.com/login",
r"https://www.yuanda76877.com/login",
r"https://www.yuanda81808.com/login",
r"https://www.yuanda86981.com/login",
r"https://www.yuanda88118.com/login",
r"https://www.yuanda99811.com/login",
r"https://tx0915.cn",
r"https://103.152.171.242",
r"https://202.146.220.100/web/#/pages/login/login",
r"https://yjow5.com/web/#/pages/login/login",
r"https://r5435.com/web/#/pages/login/login",
r"https://58w4s.com/web/#/pages/login/login",
r"https://o5oc0.com/web/#/pages/login/login",
r"https://ydqhdi.cc/auth/login",
r"https://ydqhdp.cc/auth/login",
r"https://ydqhdh.cc/auth/login",
r"https://8e7drc.nn-6.sbs/index/login/login.html",
r"https://fbhlds.nn-6.sbs/index/login/login.html",
r"https://nn-7.sbs/index/login/login.html",
r"https://yd-jk.top",
r"https://mlx65.top/index/login/login.html",
r"https://hzjufeng.top/index/login/login.html",
r"https://216.83.44.120/index/login/login.html",
r"https://yd0926.cn/index.php?m=User&a=login",
r"https://18.141.213.182/#/pages/login",
r"https://www.gkile.xyz/#/pages/login",
r"https://www.ntyef.com/#/pages/login",
r"https://www.asvbde.com",
r"https://ec2-18-141-213-182.ap-southeast-1.compute.amazonaws.com/#/pages/login",
r"https://www.yuanda12988.com/login",
r"https://www.yuanda18818.com/login",
r"https://www.yuanda19268.com/login",
r"https://www.yuanda20188.com/login",
r"https://www.yuanda36997.com/login",
r"https://www.yuanda56601.com/login",
r"https://www.yuanda61819.com/login",
r"https://www.yuanda67511.com/login",
r"https://www.yuanda67680.com/login",
r"https://www.yuanda81666.com/login",
r"https://www.yuanda81516.com/login",
r"https://www.yuanda91880.com/login",
r"https://www.yuanda15090.com/login",
r"https://www.yuanda11606.com/login",
r"https://www.yuanda70999.com/login",
r"https://steprimo.com/android/en/app/com.mega.megafundsinvest/",
r"https://yyy.fjywoowong.com/#/login​",
r"https://taikhoan-yuanta.com/#/login​",
r"https://apkpure.com/tw/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls/download/7.28.2.1216.2.827.WLS3",
r"https://www.nsdajkf.com/#/login/login",
r"https://47.129.12.212/#/login/login",
r"https://tw61.wtdiversion.com",
r"https://13.214.169.155/#/pages/login",
r"https://ec2-13-214-169-155.ap-southeast-1.compute.amazonaws.com/#/pages/login",
r"https://www.yuanda13295.com/login",
r"https://www.yuanda15888.com/login",
r"https://www.yuanda16667.com/login",
r"https://www.yuanda16818.com/login",
r"https://www.yuanda19198.com/login",
r"https://www.yuanda28185.com/login",
r"https://www.yuanda55166.com/login",
r"https://www.yuanda77107.com/login",
r"https://www.yuanda87507.com/login",
r"https://asdfghjk.fun/h5/#/",
r"https://taiwan-business-bank-co-ltd.cn.aptoide.com",
r"https://com-tbb.cn.aptoide.com",
r"https://agrdarir.top/h5/#/pages/common/login",
r"https://asdfghjk.fit/h5/#/pages/common/login",
r"https://asdfghjk.fun/h5/#/pages/common/login",
r"https://agrdarir.top/api/user/login",
r"https://asdfghjk.fun/api/user/login",
r"https://asdfghjk.fit/api/user/login",
r"https://yuanta-2024-fintech-campaign.tw/",
r"https://www.vmpkms.com/#/pages/login",
r"https://androidappsapk.co/detail-%E5%AF%8C%E9%82%A6%E5%95%86%E5%8B%99%E7%B6%B2/",
r"https://apkpure.com/%E5%9C%8B%E7%A5%A8%E8%AD%89%E5%88%B8-%E5%9C%8B%E7%A5%A8%E8%B6%85%E6%A5%AD/com.mitake.wls/download/7.33.2.1380.4.2.1012.7",
r"https://www.dhahns.com/#/pages/login",
r"https://online-com-online.es.aptoide.com",
r"https://tx1023.cn",
r"https://txjk.xyz",
r"https://www.yuanda17286.com/login",
r"https://www.yuanda36651.com/login",
r"https://www.yuanda62109.com/login",
r"https://www.yuanda66211.com/login",
r"https://www.yuanda68188.com/login",
r"https://www.yuanda76286.com/login",
r"https://www.yuanda87666.com/login",
r"https://www.yuanda88871.com/login",
r"https://www.yuanda15188.com/login",
r"https://www.yuanda19675.com/login",
r"https://www.yuanda77990.com/login",
r"https://id-yuantastock.com/#/login​",
r"https://androidappsapk.co/search/?q=com.fuhhwa.app",
r"https://sameapk.com/search/?q=com.fuhhwa.app",
r"https://www.dabnbs.com/#/pages/login",
r"https://fu-bang-e.softonic.cn/android",
r"https://fu-bang-zheng-quan-ekai-hu.softonic.cn/android",
r"https://fu-bang-zheng-quan-edian-tong.softonic.cn/android",
r"https://apkfab.com/富邦e/com.fubon.securities",
r"https://apkfab.com/日盛行動下單wts/com.sun5",
r"https://sameapk.com/日盛online/",
r"https://sameapk.com/search/?q=com.fbssks",
r"https://apkfab.com/富邦證券-e點通/com.fbs",
r"https://apkpure.com/tw/富邦證券-e點通/com.fbs",
r"https://androidappsapk.co/search/?q=com.fbssks",
r"https://apkpure.com/tw/行動下單wts/com.sun5",
r"https://apk.plus/products_富邦智選股-a70d4b9b90003e1385343feb5e4ca3b0-apk/",
r"https://fubon.goclass.tw/",
r"https://www.yuanda12957.com/login",
r"https://www.yuanda15217.com/login",
r"https://www.yuanda35501.com/login",
r"https://www.yuanda55875.com/login",
r"https://www.yuanda55959.com/login",
r"https://www.yuanda59766.com/login",
r"https://www.yuanda66018.com/login",
r"https://www.apkmonk.com/app/com.mega/",
r"https://zhao-feng-zheng-quan-xing-dong-vip.en.softonic.com/android",
r"https://com-mega.bd.aptoide.com/app",
r"https://vn-yuanta.com",
r"https://idyuantastock.com",
r"https://taikhoanyuantastock.com",
r"https://yuanda1.net/#/home",
r"https://yuandavip.net/#/register",
r"https://yuanda5.com/#/register",
r"https://yuanda6.com/#/register",
r"https://yuanda7.com/#/register",
r"https://yuanda8.com/#/register",
r"https://yuanda9.com/#/register",
r"https://yuanda12.com",
r"https://yuanda123.com",
r"https://yuanda234.com",
r"https://yuanda2.com/#/register",
r"https://yuanda3.com/#/register", 
r"https://yuanda4.com/#/register",
r"https://app.kdfute.com/web.html",
r"https://www.yuanda12698.com/login",
r"https://www.yuanda12797.com/login",
r"https://www.yuanda12801.com/login",
r"https://www.yuanda26561.com/login",
r"https://www.yuanda26987.com/login",
r"https://www.yuanda35881.com/login",
r"https://www.yuanda68610.com/login",
r"https://www.yuanda73296.com/login",
r"https://www.yuanda77109.com/login",
r"https://www.yuanda78798.com/login",
r"https://www.yuanda99617.com/login",
r"https://www.yuanda68619.com/login",
r"https://www.yuanda72188.com/login",
r"https://www.yuanda21635.com/login",
r"https://www.gqaio.com/#/pages/login",
r"https://td1112.cn/index.php?m=User&a=login",
r"https://www.androidblip.com/android-apps/com.mitake.android.landbank.html",
r"https://yad1113.cn/index.php?m=User&a=login",
r"https://apkgk.com/com.fsit.android.app",
r"https://yd1113.cn/index.php?m=User&a=login",
r"http://fb1113.cn/index.php?m=User&a=login",
r"https://tx1113.cn",
r"https://47.242.153.66",
r"https://sameapk.com/富邦投信/",
r"https://www.goslzc.com/#/pages/login",
r"https://www.tenvfdo.com/#/pages/login",
r"https://www.trsreu.com/#/pages/login",
r"https://www.krtetr.com/#/pages/login",
r"https://www.itsxmk.com/#/pages/login",
r"https://www.zloiee.com/#/pages/login",
r"https://www.kreued.com/#/pages/login",
r"https://www.losnvi.com/#/pages/login",
r"https://apkgk.com/com.tbb.mb.prod",
r"https://x51418.com.cn",
r"https://tx1120.cn",
r"https://www.yuanda12511.com/login",
r"https://www.yuanda13260.com/login",
r"https://www.yuanda16198.com/login",
r"https://www.yuanda27755.com/login",
r"https://www.yuanda62118.com/login",
r"https://www.yuanda63601.com/login",
r"https://www.yuanda68965.com/login",
r"https://www.yuanda73067.com/login",
r"https://www.yuanda73176.com/login",
r"https://www.yuanda79198.com/login",
r"https://www.yuanda35010.com/login",
r"http://www.ydhqh.com/index.html",
r"https://www.yuanda53169.com/login",
r"https://www.yuanda68981.com/login",
r"https://www.djhabf.com/#/login/login",
r"https://tx1121.cn",
r"https://tx1122.cn",
r"https://napkforpc.com/apk/com.mega.pad/",
r"https://apk.support/download-app/com.mega/126/7.33.2.1397.MEGA3.2.1031.MEGA4",
r"https://yda1124.cn/index.php?m=User&a=login​",
r"https://47.57.232.100/index.php?m=User&a=login​",
r"https://guo-piao-zheng-quan-guo-piao-chao-ye.fr.softonic.com/android",
r"https://appstorespy.com/android-google-play/com.wlf.x3mobile-trends-revenue-statistics-downloads-ratings",
r"https://www.tiospzz.com/",
r"https://tx11223.cn",
r"https://tx1126.cn",
r"https://www.wd1127.cn/index.php?m=User&a=login",
r"https://www.tx1115.cn/index.php?m=User&a=login",
r"https://hf1113.cn/index.php?m=User&a=login",
r"https://www.fb1125.cn/index.php?m=User&a=login",
r"https://www.tx1121.cn/index.php?m=User&a=login",
r"https://www.xz1127.cn/index.php?m=User&a=login",
r"https://www.x51418.com.cn/index.php?m=User&a=login",
r"https://www.hz1120.cn/index.php?m=User&a=login",
r"https://hz1126.cn/index.php?m=User&a=login",
r"https://hz1120.cn/index.php?m=User&a=login",
r"https://tx1129.cn",
r"https://tw.qh5892.bond/index/login/index",
r"https://androidappsapk.co/search/?q=com.fsit.android.app",
r"https://yd1202.cn/index.php?m=User&a=login",
r"https://apksos.com/app/com.fubon.aibank",
r"https://www.yuanda17815.com/login",
r"https://www.yuanda19621.com/login",
r"https://www.yuanda26098.com/login",
r"https://www.yuanda27399.com/login",
r"https://www.yuanda36012.com/login",
r"https://www.yuanda58559.com/login",
r"https://www.yuanda61081.com/login",
r"https://www.yuanda75088.com/login",
r"https://www.yuanda77858.com/login",
r"https://www.yuanda93958.com/login",
r"https://td1127.cn/index.php?m=User&a=login",
r"https://tx1130.cn",
r"https://1.remitano998.com/#/login​",
r"https://1.byowolngb.vip/#/login",
r"https://www.fnmdkd.com/#/pages/login",
r"https://fb1206.cn/index.php?m=User&a=login"]
    
    results = batch_analyze_urls(urls_to_test[-100:][::-1])
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
    
    