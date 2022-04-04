# -*- coding: utf-8 -*-
"""
Created on Tue Mar 22 14:16:33 2022
for BD report 
@author: LZHANG 
"""

from selenium import webdriver
import time
from lxml import etree
import re
import copy
import tqdm
import pandas as pd
import os
import hashlib
driver_path = r'C:\Users\DHU_Z\Downloads\chromedriver_win32\chromedriver.exe'

def get_one_page(url):
    homepage = webdriver.Chrome(executable_path = driver_path)
    
    homepage.get(url)
    
    page = homepage.page_source
    tree = etree.HTML(page)
    
    q = tree.xpath(r'//div[@class="panel_area"]//tbody/tr[@class="customtbl"]/td[@class="customtbl"]/span')
    revenue = []
    rank = []
    count = True
    for i in q:
        if count:
            revenue.append(i.text)
        else:
            rank.append(i.text)
        count = not count 
    
    q = tree.xpath(r'//div[@class="panel_area"]//tbody/tr[@class="customtbl"]/td[@class="customtbl"]/a')
    date = []
    for i in q:
        date.append(i.text)
    game_name =  tree.xpath(r'//h2[@id="content_2_0"]')[0].text
    q = tree.xpath(r'//form[@action="https://game-i.daa.jp/#monetize"]//p/a')
    karin_type=[]
    for i in q:
        karin_type.append(i.text)
    q = tree.xpath(r'//div[@id="monetizeTags"]/div/label/div/span')
    kakin_type_all = [i.text for i in q]
    
    
    game = {'game':game_name,'date':date,'revenue':revenue,'rank':rank,'kakin_type':karin_type}
    return game,kakin_type_all

def confirm_to_revenue(revenue,rank,kakin,game):
    if revenue is None:
        revenue = pd.DataFrame(columns = ['game'] + game['date'])
    if rank is None:
        rank = pd.DataFrame(columns = ['game'] + game['date'])
    if kakin is None:
        kakin = pd.DataFrame(columns = ['game'] + game['kakin_type'])
    re = {}
    ra = {}
    re['game'],ra['game'] = game['game']
    for i in range(len(game['date'])):
        re[game['date'][i]] = game['revenue'][i]
        ra[game['date'][i]] = game['rank'][i]
    ka = {}
    for i in game['kakin_type']:
        ka[i] = 1
    
    revenue.append(re,ignore_index = True)
    rank.append(ra,ignore_index = True)
    kakin.append(ka,ignore_index = True)
    
    return revenue,rank,kakin



homepage = webdriver.Chrome(executable_path =driver_path)
homepage.get(r'https://game-i.daa.jp/?GooglePlay%E3%82%A2%E3%83%97%E3%83%AA%E6%9C%80%E6%96%B0%E3%82%BB%E3%83%BC%E3%83%AB%E3%82%B9%E3%83%A9%E3%83%B3%E3%82%AD%E3%83%B3%E3%82%B0')
games_list  = homepage.page_source
tree = etree.HTML(games_list)
poi = tree.xpath(r'//div[@class="ie5" and @style="height: auto !important;"]//td[@class="style_td"]/strong/a/@href')
get_one_page(poi[0])
reven = None
rank = None
kakin = None
count = 0
for i in poi:
    game,kakin_type_all = get_one_page(i)
    reven,rank,kakin = confirm_to_revenue(reven,count,kakin,game)
    count += 1    
    if count > 3:
        break

rank.to_csv(r'C:\Users\DHU_Z\OneDrive\文档\bandai kadai\rank.csv')
reven.to_csv(r'C:\Users\DHU_Z\OneDrive\文档\bandai kadai\revenue.csv')
kakin.to_csv(r'C:\Users\DHU_Z\OneDrive\文档\bandai kadai\kakin.csv')
    


