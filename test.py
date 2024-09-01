import requests


top_web = ['Google.com.tw',
            'Gamer.com.tw',
            'pchome.com.tw',
            'MomoShop.com.tw',
            'ltn.com.tw',
            'Books.com.tw',
            'tvbs.com.tw',
            '104.com.tw',
            'ItHome.com.tw',
            'Yahoo.com.tw',
            'BigGo.com.tw',
            'ruten.com.tw',
            '7-11.com.tw',
            '591.com.tw',
            'cathaybk.com.tw',
            'RakuTen.com.tw',
            'bnext.com.tw',
            'cna.com.tw',
            'TaiShinBank.com.tw',
            '1111.com.tw',
            'BusinessWeekly.com.tw',
            'TaiwanLottery.com.tw',
            '4gamers.com.tw',
            'gvm.com.tw',
            'esunbank.com.tw',
            'costco.com.tw',
            'cht.com.tw',
            'cnbeta.com.tw',
            'nccc.com.tw',
            'kocpc.com.tw',
            'ecpay.com.tw',
            '8591.com.tw',
            'ShopBack.com.tw',
            'BusinessToday.com.tw',
            'Bot.com.tw',
            'CommonHealth.com.tw',
            '518.com.tw',
            'ctee.com.tw',
            'FoodPanda.com.tw',
            'Parenting.com.tw',
            'pcone.com.tw',
            'PopDaily.com.tw',
            'pcstore.com.tw',
            'FeeBee.com.tw',
            'taipeifubon.com.tw',
            'mrmad.com.tw',
            'cw.com.tw',
            'hncb.com.tw',
            'ikea.com.tw',
            'ManagerToday.com.tw',
            'heho.com.tw',
            'uwccb.com.tw',
            'CarRefOur.com.tw',
            'etmall.com.tw',
            'WalkerLand.com.tw',
            'eprice.com.tw',
            '8891.com.tw',
            'twse.com.tw',
            'ftvnews.com.tw',
            'upc.com.tw',
            'eztravel.com.tw',
            'trplus.com.tw',
            'EmailCash.com.tw',
            'Buy123.com.tw',
            'u-car.com.tw',
            'gamme.com.tw',
            'Vogue.com.tw',
            'TaiwanNews.com.tw',
            'Backpackers.com.tw',
            'BabyHome.com.tw',
            'ShoppingDesign.com.tw',
            'ColAtour.com.tw',
            'FirstBank.com.tw',
            'StockFeel.com.tw',
            'rakuya.com.tw',
            '12cm.com.tw',
            'Inside.com.tw',
            'ubot.com.tw',
            '609.com.tw',
            'tbb.com.tw',
            'pxmart.com.tw',
            'tcb-bank.com.tw',
            'AuchEntoShan.com.tw',
            'ivideo.com.tw',
            'pcsc.com.tw',
            'obdesign.com.tw',
            'thsrc.com.tw',
            'FindCompany.com.tw',
            'CathaySec.com.tw',
            'BookWalker.com.tw',
            'SkyScanner.com.tw',
            'GameBase.com.tw',
            'ItsFun.com.tw',
            'DigiTimes.com.tw',
            'MarieClaire.com.tw',
            't-cat.com.tw',
            'bahamut.com.tw',
            'hct.com.tw',
            'taifex.com.tw',
            'leju.com.tw',
            ]



def first_level_search(query_domain:str) -> str:
    a=True
    # make GET request to whois_url
    whois_url = "https://www.whois.com/whois"
    req_url = whois_url + '/' + query_domain
    try:
        first_req = requests.get(req_url)
    except requests.exceptions.RequestException as e:
        print(e)
        exit(1)

    # Extract whois content for later use
    delete_head = first_req.text.find("Domain Name: ")
    black_list = ["</div>", "</pre>", "&gt;&gt;"]
    find_tail = [first_req.text[delete_head:].find(key) for key in black_list]
    delete_tail = min([i + delete_head for i in find_tail if i != -1])
    return_data = first_req.text[delete_head: delete_tail]
    
    # extracting whois_server and registrar from the response 
    data = return_data.split('\n')
    for line in data:
        if "Registrar WHOIS Server: " in line:
            a=False
    
    if a:
        print(f'{query_domain} cannot found.')

for i in top_web:
    first_level_search(i)