# -*- coding:utf-8 -*-

import eventlet
import requests
import re
import pymysql as mysql
import pandas as pd
import json
from lxml import etree



def CjmRuqests(url):
    data = {
        "url": url,
        "isnewspaper": "0",
        "html": ""
    }
    api = "http://192.168.20.219:5555/CJMExtractionComponent"
    resp = requests.post(api,data)
    detail_data = resp.json()
    detail_data = json.dumps(detail_data)
    # print(detail_data)
    return detail_data.encode('utf-8').decode('unicode_escape')
def clean(source):
    try:
        source = source.strip(">,<,-,：,: ")
        source = source.strip("来源：")
        source=source.strip()
        return source
    except:
        return source
def find_metasource(web_content):
    try:
        """
           html_d是原始的html
           1、id 获取id 的属性值
           2、starts-with 顾名思义，匹配一个属性开始位置的关键字 – 模糊定位
           3、contains 匹配一个属性值中包含的字符串 – 模糊定位
           4、text() 函数文本定位
           5、last() 函数位置定位
           """
        data_html = etree.HTML(web_content)
        # source_list = data_html.xpath("//span[contains(text(), \"来源\"")
        # source_list = data_html.xpath("//span[starts-with(@name,'source')]")
        source_list = data_html.xpath("//meta[contains(@name, 'Source')]")
        print(3)
        for source_tree in source_list:
            source = "".join(source_tree.xpath("./@content")).strip()
        return source
    except:
        return None
def find_sourceInline(web_content):
    if re.search(r"来源[：\-:]\s*[\u4e00-\u9fa5]+",web_content,re.M|re.I) is not None:
        detail= re.search(r"来源[：\-:]\s*[\u4e00-\u9fa5]+",web_content,re.M|re.I)
    elif re.search(r"来源[：\-:]\s*(<.*?>)*[\u4e00-\u9fa5]+",web_content,re.M|re.I) is not None:
        detail= re.search(r"来源[：\-:]\s*(<.*?>)*[\u4e00-\u9fa5]+",web_content,re.M|re.I)
    else:
        detail = re.search(r">*\s*[　]*来源\s*[：\-:](</em>)*\s*(<.*?>)*[《|“]*[\u4e00-\u9fa5]+[》|”|－|-|·]*(\w+)*(\s|<|】|-)",
                       web_content, re.M | re.I)
    if detail is not None:
        source = detail[0]
        jian = re.search(r"<.*>", detail[0])
        if jian is not None:
            source = source.replace(jian[0], " ")
        source =clean(source)
    else:
        source="None"
    return source
def get_source(url):
    try:
        with eventlet.Timeout(20,True):
            web_content=CjmRuqests(url)
    except:
        return "timeout"
        pass
    source1 = find_sourceInline(web_content)
    source2 = find_metasource(web_content)
    if source1 != source2 and source2 is not None and source2 !="":
        source = source2
    else:
        source = source1
    return source

save_excel=r"source2.xlsx"

con = mysql.connect(host="192.168.20.147",port=3306,user="jgw",passwd="Jgw*31500-2018.6",db="cjm_spider_seed",charset="utf8mb4")
mycursor = con.cursor()
print("连接成功")

sql = "SELECT id,url,web_source FROM extraction_test_source  where id>520000 and id <= 522000 and health_degree > 60"
df = pd.read_sql(sql, con=con)

for i in range(df.__len__()):
    eventlet.monkey_patch()
    try:
        with eventlet.Timeout(20,True):
            url = df["url"].iloc[i]
            source = get_source(url)
            print(source)
            df["web_source"].iloc[i]=source
    except eventlet.timeout.Timeout:
        df["web_source"].iloc[i] = "timeout"
        pass
    except Exception:
        df.to_excel(save_excel)

df.to_excel(save_excel)




