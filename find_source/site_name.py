import time
from io import BytesIO

import requests
from PIL import Image
import pytesseract
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tldextract
import pandas as pd
from tqdm import tqdm
import requests,json
import pymysql as mysql

edge=r'C:\Users\PC\ppp\Scripts\msedgedriver.exe'


# 获得域名
def domain_extraction(url):
    val = tldextract.extract(url)
    domain = val.subdomain + "." + val.domain + "." + val.suffix
    return domain

# 获得验证码图片，保存在同级目录下的fetch_data.png
def get_img2(driver):
    driver.save_screenshot('fetch_data.png')  # 截取整个DOC

    width = 'return document.body.clientWidth'
    w = driver.execute_script(width)
    hight = 'return document.body.clientHeight'
    h = driver.execute_script(hight)

    im = Image.open("fetch_data.png")
    new_im = im.resize((w, h))
    # new_im.show()

    ce = driver.find_element(By.XPATH, '//*[@id="domainform"]/div/div[2]/div/img')
    left = ce.location['x'] - 10
    top = ce.location['y']
    right = ce.size['width'] + left
    height = ce.size['height'] + top

    img = new_im.crop((left, top, right, height))
    img.save('fetch_data.png')
    # img.show()
    return img

# 识别验证码
def reg_num():
    return pytesseract.image_to_string(Image.open('fetch_data.png'), lang='eng')

# 爬取table，返回字典
def get_table(driver):
    info = {}
    table_tr_list1 = driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[3]/div[1]/table').find_elements(
        By.TAG_NAME, 'tr')
    for tr in table_tr_list1:
        td_list = tr.find_elements(By.TAG_NAME, 'td')
        info[td_list[0].text] = td_list[1].text

    table_tr_list2 = driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div[3]/div[2]/table').find_elements(
        By.TAG_NAME, 'tr')
    for tr in table_tr_list2:
        td_list = tr.find_elements(By.TAG_NAME, 'td')
        info[td_list[0].text] = td_list[1].text
    return info

# 利用API提取网站单位
def api_info(url):
    try:
        api_url = 'http://192.168.20.219:5660/domain_info?urlinfo=' + url
        res = requests.get(api_url).text
        tokenJson = json.loads(res)
        loc = tokenJson['site_info']['Whois_INFO']['网站单位']
        if loc != None:
            return loc
        else:
            try:
                api_url = 'http://192.168.20.219:5660/domain_vip?urlinfo=' + url
                res = requests.get(api_url).text
                tokenJson = json.loads(res)
                loc = tokenJson['site_info']['Whois_INFO']['网站单位']
                if loc != None:
                    return loc
                else:
                    return ""
            except:
                return ""
    except:
        try:
            api_url = 'http://192.168.20.219:5660/domain_vip?urlinfo=' + url
            res = requests.get(api_url).text
            tokenJson = json.loads(res)
            loc = tokenJson['site_info']['Whois_INFO']['网站单位']
            if loc != None:
                return loc
            else:
                return ""
        except:
            return ""

def get_name(url, driver):
    driver.get('https://www.beian.gov.cn/portal/registerSystemInfo')
    flag = 0
    while True:
        driver.refresh()
        try:
            WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH, '/html/body/div[1]/div[3]/div'))
        except:
            break

        try:
            # 找到网站域名选项
            web = driver.find_element(By.XPATH, '//*[@id="myTab"]/li[2]/a').click()
            # 找到URL框
            url_input = driver.find_element(By.XPATH, '//*[@id="domain"]')
            url_input.send_keys(Keys.CONTROL + 'a')
            url_input.send_keys(Keys.BACK_SPACE)
            url_input.send_keys(url)

            # 等待验证码出现
            WebDriverWait(driver, 10).until(
                lambda x: x.find_element(By.XPATH, '//*[@id="domainform"]/div/div[2]/div/img'))
            img_src = driver.find_element(By.XPATH, '//*[@id="domainform"]/div/div[2]/div/img').get_attribute('src')
            # img_base64 = get_img(img_src)
            img = get_img2(driver)
            num = reg_num()
            # print(num)
            num_input = driver.find_element(By.XPATH, '//*[@id="ver2"]').send_keys(num)
            time.sleep(1)

            if driver.find_element(By.XPATH, '//*[@id="domainerror"]').is_displayed():
                continue
            elif driver.find_element(By.XPATH, '//*[@id="domainright"]').is_displayed():
                # 点击查询
                botton = driver.find_element(By.XPATH, '//*[@id="domainform"]/div/div[3]/div/button').click()
                time.sleep(3)

            if driver.find_element(By.XPATH, '//*[@id="a_wzym"]').text == '没有查到数据!':
                flag = 1
                break

        except:
            break

    if flag == 0:
        return get_table(driver)['网站名称'], 2
    else:
        return api_info(url), 3

# 直接解析网站HTML，返回网站名称列表，数据来源列表
# 返回state
#   1 代表可以提取到网站的title，
#   0 代表无法通过HTML提取到title，或者网页解析失败
def get_site_name(ids, urls, site_names):
    options = webdriver.Edge
    options.page_load_strategy = 'none'
    driver = webdriver.Edge(r'C:\Users\PC\ppp\Scripts\msedgedriver.exe')
    driver.maximize_window()

    wait = WebDriverWait(driver, 5)
    names = []
    state = []
    for i in tqdm(range(len(urls))):
       try:
           url = urls[i]
           driver.get(url)
           WebDriverWait(driver, 10).until(
               EC.invisibility_of_element(driver.find_element(By.XPATH, '/html/head/title')))

           title = driver.find_element(By.XPATH, '/html/head/title').get_attribute("textContent")
           print(title)
           title = title.replace("首页", "")
           title = title.replace(" ", "")
           title = title.replace("-","")
           names.append(title)
           state.append(1)
       except:
           title = site_names[i]
           names.append(title)
           state.append(0)
    return pd.DataFrame({'id': ids, 'url': urls, 'site_name': site_names, 'title': names, 'state': state})

# 返回网站名称列表，数据来源列表
# 返回info的网站名，若未查询成功则为""；
# 返回state
#   2 代表数据查询于https://www.beian.gov.cn/portal/registerSystemInfo
#   3 代表查询于接口api
def get_site_name2(domains):
    options = webdriver.ChromeOptions()
    driver = webdriver.Edge(edge)
    driver.maximize_window()
    site_names = []
    states = []
    for i in tqdm(range(len(domains))):
        domain = domains[i]
        info, state = get_name(domain, driver)
        states.append(state)
        site_names.append(info)
        print(domain, info, state)
    return site_names, states

# 判定是否有中文
def is_Chinese(ch):
    if '\u4e00' <= ch <= '\u9fff':
        return True
    return False

if __name__ == "__main__":
    df=pd.read_csv("site_data.csv")
    print(df)
    for i in range(df.__len__()):
        if df["state"].iloc[i] == 1:
            try:
                print(requests.get(df["url"].iloc[i]))
            except:
                print("false")
            else:
                print(df["url"].iloc[i])


    # 连接数据库
    con = mysql.connect(host="192.168.20.147",port=3306,user="jgw",passwd="Jgw*31500-2018.6",db="cjm_spider_seed",charset="utf8mb4")
    mycursor = con.cursor()
    print("连接成功")

    sql = "select * from data_source_copy3_copy1 where done=0 and site_name is null "
    df = pd.read_sql(sql, con=con)

    # 直接html解析title
    site_data = get_site_name(df['id'], df['url'], df['site_name'])
    print(site_data)
    site_data['title'] = site_data['title'].fillna("")
    site_data.to_csv("site_data.csv", index=0)

    # 获取问题数据段
    # 若是英文，则暂时用原式site_name代替
    # 若title为空，采用网站和API获取网站单位
    for i in range(len(site_data)):
        ids = []
        site_names = []
        domains = []
        ids.append(site_data['id'][i])
        site_names.append(site_data['title'][i])
        domains.append(domain_extraction(site_data['url'][i]))

    # for i in range(len(site_data)):
    #     if not is_Chinese(site_data['title'][i]) and is_Chinese(site_data['site_name'][i]):
    #         site_data.loc[i, 'title'] = site_data.loc[i, 'site_name']
    #
    #     if (not is_Chinese(site_data['title'][i])) or (site_data['title'][i] == ""):
    #         ids.append(site_data['id'][i])
    #         site_names.append(site_data['title'][i])
    #         domains.append(domain_extraction(site_data['url'][i]))

    # 通过网站和API获得title
    new_site_names, sources = get_site_name2(domains)

    for i in range(len(ids)):
        site_data.loc[site_data['id'] == ids[i], 'title'] = new_site_names[i]
        site_data.loc[site_data['id'] == ids[i], 'state'] = sources[i]

    # 进一步处理title
    for i in range(len(site_data)):
        title = site_data.loc[i, 'title']
        # 空值或英文，用原始代替，原始为空值或英文，则title保持空值
        if (title == "") or (not is_Chinese(title)):
            if is_Chinese(site_data['site_name'][i]):
                title = site_data.loc[i, 'site_name']
            else:
                title = ""
        else:
            # 去除-等符号，取出前缀
            prefix1 = site_data['title'][i].split("_")[0]
            title = prefix1

            # 去除_，取出前缀
            prefix2 = site_data['title'][i].split("_")[0]
            title = prefix2

            # 去除“门户网站”
            title = title.replace("门户网站", "")

            # 去除“首页”
            title = title.replace("首页", "")
        site_data.loc[i, 'title'] = title

    site_data.to_csv("new_site_data.csv",index=0)


