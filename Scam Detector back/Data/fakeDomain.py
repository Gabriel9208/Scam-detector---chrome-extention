from sklearn.feature_extraction.text import TfidfVectorizer
from Levenshtein import distance
import re
import numpy as np
# from selenium import webdriver

# chromeOpt = webdriver.ChromeOptions()
# chromeOpt.add_argument("--headless=new")  
# chromeOpt.add_argument("--disable-gpu")
# chromeOpt.add_argument("--no-sandbox")
# chromeOpt.add_argument('--blink-settings=imagesEnabled=false')

    
# driver = webdriver.Chrome(options=chromeOpt)

html_tags = ['script', 'style', 'noscript', 'iframe', 'object', 'embed', 'span', 'div', 'p', 'a', 'button', 'input', 'textarea', 'select', 'option', 'label', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'form', 'fieldset', 'legend']
html_tag_attributes = ['id', 'style', 'href', 'src', 'data-src', 'lang', 'title', 'alt', 'aria', 'label', 'name', 'rel', 'target', 'onclick', 'onload', 'type', 'placeholder', 'role', 'tabindex', 'value']

def check_fake_domain(user_url, document):
    """
    Analyzes similarity between domains and webpage content to detect potential phishing.
    
    Args:
        user_url (str): The legitimate URL to compare against
        potential_phishing_url (str): The suspicious URL to analyze
    
    Returns:
        tuple: (similarity_score, is_suspicious, important_words)
    """
    user_domain = extract_domain(user_url)
    
    try:
        redFlag = False
        important_words = extract_important_words(document, domain=[user_domain.lower()])
        
        threshold = len(user_domain) * 0.2 if len(user_domain) >= 5 else 1
        
        for idx, word in enumerate(important_words):
            d = distance(user_domain, word)
            if d > 0 and d <= threshold:
                redFlag = True
            if d == 0:
                print(idx)
                return False
            
        return redFlag
        
    except Exception as e:
        print(f"Error analyzing URLs: {e}")
        return False

def extract_domain(url):
    """Extracts domain from URL"""
    domain = re.sub(r'https?://', '', url)
    TLD_LIST = [
        # Generic TLDs
        'com', 'net', 'org', 'info', 'biz', 'name', 'pro',
        
        # Sponsored TLDs
        'aero', 'asia', 'cat', 'coop', 'edu', 'gov', 'int', 'jobs', 'mil', 'mobi', 
        'museum', 'post', 'tel', 'travel', 'xxx',
        
        # Country code TLDs
        'ac', 'ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq', 'ar', 
        'as', 'at', 'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 
        'bh', 'bi', 'bj', 'bl', 'bm', 'bn', 'bo', 'bq', 'br', 'bs', 'bt', 'bv', 
        'bw', 'by', 'bz', 'ca', 'cc', 'cd', 'cf', 'cg', 'ch', 'ci', 'ck', 'cl', 
        'cm', 'cn', 'co', 'cr', 'cu', 'cv', 'cw', 'cx', 'cy', 'cz', 'de', 'dj', 
        'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 'eh', 'er', 'es', 'et', 'eu', 
        'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 
        'gh', 'gi', 'gl', 'gm', 'gn', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 
        'gy', 'hk', 'hm', 'hn', 'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 
        'io', 'iq', 'ir', 'is', 'it', 'je', 'jm', 'jo', 'jp', 'ke', 'kg', 'kh', 
        'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz', 'la', 'lb', 'lc', 'li', 
        'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md', 'me', 'mf', 
        'mg', 'mh', 'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms', 'mt', 
        'mu', 'mv', 'mw', 'mx', 'my', 'mz', 'na', 'nc', 'ne', 'nf', 'ng', 'ni', 
        'nl', 'no', 'np', 'nr', 'nu', 'nz', 'om', 'pa', 'pe', 'pf', 'pg', 'ph', 
        'pk', 'pl', 'pm', 'pn', 'pr', 'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 
        'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd', 'se', 'sg', 'sh', 'si', 'sj', 
        'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'ss', 'st', 'su', 'sv', 'sx', 'sy', 
        'sz', 'tc', 'td', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 
        'tp', 'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk', 'um', 'us', 'uy', 
        'uz', 'va', 'vc', 've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ws', 'ye', 'yt', 
        'za', 'zm', 'zw',
        
        # New gTLDs
        'academy', 'accountant', 'accountants', 'active', 'actor', 'ads', 'adult',
        'agency', 'airforce', 'apartments', 'app', 'army', 'art', 'associates', 'attorney',
        'auction', 'audio', 'auto', 'band', 'bank', 'bar', 'bargains', 'bayern', 'beer',
        'berlin', 'best', 'bet', 'bid', 'bike', 'bingo', 'bio', 'black', 'blackfriday',
        'blog', 'blue', 'boutique', 'broker', 'build', 'builders', 'business', 'buzz',
        'cab', 'cafe', 'camera', 'camp', 'capital', 'car', 'cards', 'care', 'career',
        'careers', 'cars', 'casa', 'cash', 'casino', 'catering', 'center', 'ceo',
        'charity', 'chat', 'cheap', 'church', 'city', 'claims', 'cleaning', 'clinic',
        'clothing', 'cloud', 'club', 'coach', 'codes', 'coffee', 'college', 'community',
        'company', 'computer', 'condos', 'construction', 'consulting', 'contractors',
        'cooking', 'cool', 'country', 'coupons', 'courses', 'credit', 'creditcard',
        'cricket', 'cruises', 'dance', 'date', 'dating', 'deals', 'degree', 'delivery',
        'democrat', 'dental', 'dentist', 'design', 'dev', 'diamonds', 'diet', 'digital',
        'direct', 'directory', 'discount', 'doctor', 'dog', 'domains', 'download',
        'earth', 'education', 'email', 'energy', 'engineer', 'engineering', 'enterprises',
        'equipment', 'estate', 'events', 'exchange', 'expert', 'exposed', 'express',
        'fail', 'faith', 'family', 'fans', 'farm', 'fashion', 'film', 'finance',
        'financial', 'fish', 'fishing', 'fit', 'fitness', 'flights', 'florist',
        'flowers', 'foo', 'football', 'forex', 'forsale', 'foundation', 'fund',
        'furniture', 'futbol', 'fyi', 'gallery', 'game', 'games', 'garden', 'gdn',
        'gift', 'gifts', 'gives', 'glass', 'global', 'gmbh', 'gold', 'golf', 'graphics',
        'gratis', 'green', 'gripe', 'group', 'guide', 'guitars', 'guru', 'hair',
        'hamburg', 'haus', 'health', 'healthcare', 'help', 'hiphop', 'hockey', 'holdings',
        'holiday', 'homes', 'horse', 'hospital', 'host', 'hosting', 'house', 'how',
        'immo', 'immobilien', 'industries', 'ink', 'institute', 'insure', 'international',
        'investments', 'irish', 'jewelry', 'juegos', 'kaufen', 'kim', 'kitchen',
        'kiwi', 'land', 'lawyer', 'lease', 'legal', 'life', 'lighting', 'limited',
        'limo', 'link', 'live', 'loan', 'loans', 'lol', 'london', 'love', 'ltd',
        'luxury', 'maison', 'management', 'market', 'marketing', 'markets', 'mba',
        'media', 'memorial', 'men', 'menu', 'miami', 'moda', 'moe', 'mom',
        'money', 'mortgage', 'moscow', 'movie', 'navy', 'network', 'news', 'ninja',
        'nyc', 'observer', 'one', 'onl', 'online', 'ooo', 'page', 'paris', 'partners',
        'parts', 'party', 'pet', 'pets', 'pharmacy', 'photo', 'photography', 'photos',
        'pics', 'pictures', 'pink', 'pizza', 'place', 'plumbing', 'plus', 'poker',
        'porn', 'press', 'productions', 'promo', 'properties', 'property', 'protection',
        'pub', 'qpon', 'racing', 'radio', 'recipes', 'red', 'rehab', 'reise', 'reisen',
        'rent', 'rentals', 'repair', 'report', 'republican', 'rest', 'restaurant',
        'review', 'reviews', 'rich', 'rip', 'rocks', 'rodeo', 'run', 'sale', 'salon',
        'sarl', 'school', 'schule', 'science', 'security', 'services', 'sex', 'sexy',
        'shiksha', 'shoes', 'shop', 'shopping', 'show', 'singles', 'site', 'ski',
        'soccer', 'social', 'software', 'solar', 'solutions', 'soy', 'space', 'sport',
        'sports', 'spot', 'srl', 'store', 'stream', 'studio', 'study', 'style',
        'sucks', 'supplies', 'supply', 'support', 'surf', 'surgery', 'systems',
        'tattoo', 'tax', 'taxi', 'team', 'tech', 'technology', 'tennis', 'theater',
        'theatre', 'tickets', 'tienda', 'tips', 'tires', 'today', 'tools', 'top',
        'tours', 'town', 'toys', 'trade', 'trading', 'training', 'tube', 'tv',
        'university', 'uno', 'vacations', 'vegas', 'ventures', 'vet', 'viajes',
        'video', 'villas', 'vin', 'vip', 'vision', 'vodka', 'vote', 'voting',
        'voyage', 'watch', 'webcam', 'website', 'wedding', 'wiki', 'win', 'wine',
        'work', 'works', 'world', 'wtf', 'xyz', 'yoga', 'zone',
    ]
    
    
    domain = domain.split('/')[0]
    levelDomain = domain.split('.')
    skip = 0
    for i in range(len(levelDomain))[::-1]:
        if levelDomain[i] not in TLD_LIST:
            skip = i
            break
    
    if skip == 0:
        return levelDomain[0]
    
    return levelDomain[skip]


def extract_important_words(documents, max_features=100, domain=None):
    """Extracts important words using TF-IDF"""
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        stop_words=html_tags + html_tag_attributes,
        lowercase=True,
    )
    
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    
    # Average TF-IDF score
    avg_scores = np.mean(tfidf_matrix.toarray(), axis=0)
    
    important_indices = avg_scores.argsort()[-15:][::-1]
    return [feature_names[i] for i in important_indices]

def fakeDomainDetection(url, page_source):
    # driver.get(url)
    ps = re.sub(r'<script[\s\S]*?</script>', '', page_source.lower())
    ps = re.sub(r'<style[\s\S]*?</style>', '', ps)
    ps = re.sub(r'{[\s\S]*}', '', ps)
    ps = re.sub(r'class="[\s\S]*?"', '', ps)
    ps = re.sub(r'style="[\s\S]*?"', '', ps)
    ps = re.sub(r'(https|http|www|)', '', ps)
    ps = re.sub(r'([a-z0-9])([\u4e00-\u9fff])', r'\1 \2', ps)  
    ps = re.sub(r'([\u4e00-\u9fff])([a-z0-9])', r'\1 \2', ps)  # Add space between Chinese and Latin/numbers
    ps = re.sub(r'\s+', ' ', ps)
    ps = ps.strip()
            

    l = len(ps)
    if l == 0:
        return {"result": False, "message": "The domain is legitimate"}
    
    document = [ps[i:i+l//4] for i in range(0, l, l//4)]
    if(check_fake_domain(url.lower(), document)):
        return {"result": True, "message": "The domain is suspicious"}
    else:
        return {"result": False, "message": "The domain is legitimate"}
    


if __name__ == "__main__":
    

    # url = [
    #     "https://www.google.com.tw/",
    #     "https://www.gamer.com.tw/",
    #     "https://www.pchome.com.tw/",
    #     "https://www.momoshop.com.tw/",
    #     "https://www.ltn.com.tw/",
    #     "https://www.books.com.tw/",
    #     "https://www.tvbs.com.tw/",
    #     "https://www.104.com.tw/",
    #     "https://www.ithome.com.tw/",
    #     "https://tw.yahoo.com/",
    #     "https://biggo.com.tw/",
    #     "https://www.ruten.com.tw/",
    #     "https://www.7-11.com.tw/",
    #     "https://www.591.com.tw/",
    #     "https://www.cathaybk.com.tw/cathaybk/",
    #     "https://www.rakuten.com.tw/",
    #     "https://www.bnext.com.tw/",
    #     "https://www.cna.com.tw/",
    #     "https://www.taishinbank.com.tw/",
    #     "https://www.1111.com.tw/",
    #     "https://www.businessweekly.com.tw/",
    #     "http://www.taiwanlottery.com.tw/",
    #     "https://www.4gamers.com.tw/",
    #     "https://www.gvm.com.tw/",
    #     "https://www.esunbank.com.tw/",
    #     "https://www.costco.com.tw/",
    #     "https://www.cht.com.tw/",
    #     "https://www.cnbeta.com.tw/",
    #     "https://www.nccc.com.tw/wps/wcm/connect/en/home",
    #     "https://www.kocpc.com.tw/",
    #     "https://www.ecpay.com.tw/",
    #     "https://www.8591.com.tw/",
    #     "https://www.shopback.com.tw/",
    #     "https://www.businesstoday.com.tw/",
    #     "https://www.bot.com.tw/",
    #     "https://www.commonhealth.com.tw/",
    #     "https://www.518.com.tw/",
    #     "https://www.ctee.com.tw/",
    #     "https://www.foodpanda.com.tw/",
    #     "https://www.parenting.com.tw/",
    #     "https://www.pcone.com.tw/",
    #     "https://www.popdaily.com.tw/",
    #     "https://m.pcstore.com.tw/",
    #     "https://feebee.com.tw/",
    #     "https://ebank.taipeifubon.com.tw/",
    #     "https://mrmad.com.tw/",
    #     "https://english.cw.com.tw/",
    #     "https://www.hncb.com.tw/",
    #     "https://www.ikea.com/tw/",
    #     "https://www.managertoday.com.tw/",
    #     "https://heho.com.tw/",
    #     "https://sslpayment.uwccb.com.tw/EPOSPortal/Login.aspx",
    #     "https://www.carrefour.com.tw/",
    #     "https://www.etmall.com.tw/",
    #     "https://www.walkerland.com.tw/",
    #     "https://m.eprice.com.tw/",
    #     "https://www.8891.com.tw/",
    #     "http://www.twse.com.tw/",  
    #     "https://english.ftvnews.com.tw/",
    #     "https://www.upc.com.tw/",
    #     "https://www.eztravel.com.tw/",
    #     "https://www.trplus.com.tw/",
    #     "https://www.emailcash.com.tw/",
    #     "https://m.buy123.com.tw/",
    #     "https://m.u-car.com.tw/",
    #     "https://www.gamme.com.tw/",
    #     "https://www.vogue.com.tw/",
    #     "https://www.taiwannews.com.tw/",
    #     "https://www.backpackers.com.tw/",
    #     "https://www.babyhome.com.tw/",
    #     "https://www.shoppingdesign.com.tw/",
    #     "https://www.colatour.com.tw/home/",
    #     "https://www.firstbank.com.tw/",
    #     "https://www.stockfeel.com.tw/",
    #     "https://www.rakuya.com.tw/",
    #     "https://www.12cm.com.tw/",
    #     "https://www.inside.com.tw/",
    #     "https://www.ubot.com.tw/",
    #     "https://www.609.com.tw/",
    #     "https://www.tbb.com.tw/",
    #     "https://www.pxmart.com.tw/",
    #     "https://www.tcb-bank.com.tw/",
    #     "https://www.auchentoshan.com/",
    #     "https://www.ivideo.com.tw/english/",
    #     "https://sapportal.pcsc.com.tw/",
    #     "https://www.obdesign.com.tw/",
    #     "https://www.thsrc.com.tw/",
    #     "https://www.findcompany.com.tw/",
    #     "https://www.cathaysec.com.tw/",
    #     "https://www.bookwalker.com.tw/",
    #     "https://www.skyscanner.com.tw/",
    #     "https://news.gamebase.com.tw/",
    #     "https://itsfun.com.tw/",
    #     "https://www.digitimes.com.tw/",
    #     "https://www.marieclaire.com.tw/",
    #     "https://www.t-cat.com.tw/",
    #     "https://www.gamer.com.tw/",
    #     "https://www.hct.com.tw/",
    #     "https://www.taifex.com.tw/",
    #     "https://www.leju.com.tw/",
    # ]
    
    # with open("./result.txt", "w") as f:  
    #     for u in url:
    #         try:
    #             f.write(u + " " + str(fakeDomainDetection(u)) + "\n")
    #         except Exception as e:
    #             f.write(u + " " + "exception" + "\n" )
    
    print(fakeDomainDetection("https://tw.yahoo.com/"))
        
    # driver.quit()
