# -*- coding: utf-8 -*-
"""
Created on Mon Mar 14 16:47:13 2022

@author: lzhang
"""
from selenium import webdriver
import time
from lxml import etree
import re
import copy
import tqdm
import pandas as pd
import os
import pathlib

options = webdriver.ChromeOptions()
'''
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disabke-notifications')
'''


class crawl_mobile_games_top200(object):
    def __init__(self,host_link = r'https://play.google.com',out_put_path = r'data',executable_path = None,sql = True):
        
        self.host_link = host_link
        self.executable_path = executable_path
        self.option = webdriver.ChromeOptions()
        self.option.add_argument('headless')
        self.data_output = [os.path.join(out_put_path,'review.csv'),\
                            os.path.join(out_put_path,'game.csv')]
        self.game_links = None
        self.info = None
        self.reviews = None
        self.all_games_url = None
        
    def get_driver(self):
        
        if self.executable_path is None:
            driver = webdriver.Chrome(chrome_options=self.option)
        else:
            driver = webdriver.Chrome( executable_path = self.executable_path,\
                                      chrome_options=self.option)
        return driver
    
    def get_all_game_links(self, url):
        '''
        return all the urls of the games shown in this page, as type of 1D list []
        
        '''
        homepage = self.get_driver()
        homepage.get(url)
        '''
        scroll to buttom
        
        '''
        
        for i in range(3):
            homepage.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
        '''
        catch the urls of top 200 games
        
        '''
        
        games_list  = homepage.page_source
        tree = etree.HTML(games_list)
        homepage.close()
        self.all_games_url = [self.host_link + href + r'&hl=ja' for href in  tree.xpath(r'//div[@class="b8cIId ReQCgd Q9MA7b"]//a/@href')]
        
        return self.all_games_url
    
    
    def catch_single_page(self,url):
        
        print(url)
        
        '''
        Catch the reviews and info for 1 game
        return: game info table (1d) :game_name ,introduction, review_number, stars, developer  game_type and price
        
                review table (2d) :game_id, useful_num, score, review text, 2D list
        
        '''
        driver = self.get_driver()
        driver.get(url)
        page_text = driver.page_source
        
        '''
        click もっと見る
        
        '''
        try:
            full_intro_button = driver.find_elements_by_xpath(r'//div[@jscontroller="IsfMIf"]//div[@class="U26fgb O0WRkf oG5Srb C0oVfc n9lfJ M9Bg4d"]')
            full_intro_button[0].click()
        except:
            True
        
        '''
        start catch info: game_name ,introduction, review_number, stars, developer  game_type and price
        '''
        
        #game name
        game_name = driver.find_element_by_xpath(r'//h1[@itemprop="name"]/span').text
        #introduction
        intro_text = driver.find_elements_by_xpath(r'//div[@jsname="sngebd"]')[0].text               
        #review number
        num_of_people = driver.find_elements_by_xpath(r'//c-wiz[@jsrenderer="GxnCG"]')[0].text.replace(',','') 
        #stars
        tree = etree.HTML(driver.page_source)
        stars = driver.find_elements_by_xpath(r'//div[@class="K9wGie"]/div[@class="BHMmbe"]')[0].text
        #developer and game type
        [developer,typeofgame] = tree.xpath(r'//span[@class="T32cc UAO9ie"]/a')
        developer = developer.text                              
        typeofgame = typeofgame.text
        #game price
        kakin = driver.find_element_by_xpath(r'//div[@class="bSIuKf"]').text
        try:
            price = tree.xpath(r'//button[@class=" LkLjZd ScJHi HPiPcc IfEcue"]/@aria-label')[0]
            price = re.search(r'\d{1,}',price).group() 
        except:
            
            try :
                price = tree.xpath(r'//button[@class=" LkLjZd ScJHi HPiPcc IfEcue"]/@aria-label')[0]
                price = re.search(r'\d{1,}',price).group() 

            except:
                
                price = 0
   
        
        '''
        finished catch info
        '''
        game_id = hash(game_name)
        info = {'game_id':game_id,'game':game_name,'intro':intro_text, 'num_of_review':num_of_people, 'stars':stars,\
                'develop':developer, 'type':typeofgame,'kakin':kakin,'price':price}
        
        '''
        start catch reviews: game_id, useful_num, score, review text, 2D list
        '''

        review_href = url +r'&showAllReviews=true'
        driver.get(review_href)
        '''
        scroll to buttom
        
        '''
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        
        '''
        expand hiden message
        '''
        js_top = "var q=document.documentElement.scrollTop=0"
        
        for j in range(5):
            full_review_text_button = driver.find_elements_by_xpath(r'//button[@class="LkLjZd ScJHi OzU4dc"]')
            try:
                for i in range(len(full_review_text_button)):
                    driver.execute_script(js_top)
                    full_review_text_button[i].click()
                    time.sleep(0.1)
            except:
                break
        
        tree = etree.HTML(driver.page_source)
        '''
        get each review block
        '''
        review_block = tree.xpath(r'//div[@class="d15Mdf bAhLNe"]')

        all_review =  pd.DataFrame(columns=['game','game_id','score','useful','review_text'])
        for i in range(len(review_block)):
            blocks = copy.deepcopy(review_block[i])
            score = blocks.xpath(r'//div[@role="img"]/@aria-label')
            score = re.search(r'\d/\d',score[0]).group()  
            useful = blocks.xpath(r'//div[@class="jUL89d y92BAb"]')[0].text
            review_text = blocks.xpath(r'//span[@jsname="bN97Pc"]')[0].text
            all_review.loc[-1]=[game_name,game_id,score,useful,review_text]
            
        driver.close()
        return  info, all_review
    
    def get_all_games(self,url):
        
        urls = self.get_all_game_links(url)
        #info, reviews = [],[]
        for page in tqdm.tqdm(urls):
            i,r = self.catch_single_page(page)
            [pathlib.Path(i) for i in self.data_output]
            i.to_csv(self.data_output[0],mode = 'a')
            r.to_csv(self.data_output[1],mode = 'a')         


                      
if __name__ == '__main__':
    executable_path1 = r'E:\chromdownload\chromedriver_win32\chromedriver.exe'
    test_url1 = r'https://play.google.com/store/apps/collection/cluster?clp=0g4YChYKEHRvcGdyb3NzaW5nX0dBTUUQBxgD:S:ANO1ljLhYwQ&gsr=ChvSDhgKFgoQdG9wZ3Jvc3NpbmdfR0FNRRAHGAM%3D:S:ANO1ljIKta8&hl=ja'
    a = crawl_mobile_games_top200(executable_path = executable_path1)
    a.get_all_games(test_url1)
    
    
    
    
'''
host_link = r'https://play.google.com'
homepage = webdriver.Chrome(executable_path = r'E:\chromdownload\chromedriver_win32\chromedriver.exe')
homepage.get(r'https://play.google.com/store/apps/collection/cluster?clp=0g4YChYKEHRvcGdyb3NzaW5nX0dBTUUQBxgD:S:ANO1ljLhYwQ&gsr=ChvSDhgKFgoQdG9wZ3Jvc3NpbmdfR0FNRRAHGAM%3D:S:ANO1ljIKta8&hl=ja')
for i in range(2):
    homepage.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

games_list  = homepage.page_source
tree = etree.HTML(games_list)
def get_href(tree):
    return [host_link+href for href in  tree.xpath(r'//div[@class="b8cIId ReQCgd Q9MA7b"]//a/@href')]
    
href_list = get_href(tree)

def get_game_page(page_href):
    
    driver = webdriver.Chrome(executable_path =  executable_path)
    driver.get(page_href)
    page_text = driver.page_source
    
    full_intro_button = driver.find_elements_by_xpath(r'//div[@class="U26fgb O0WRkf oG5Srb C0oVfc n9lfJ M9Bg4d" and @aria-label="もっと見る"]')
    full_review_button = driver.find_elements_by_xpath(r'//div[@class="U26fgb O0WRkf oG5Srb C0oVfc n9lfJ M9Bg4d" and @jsname="wmgIXe"]')
    tree = etree.HTML(page_text)
    name_list = tree.xpath(r'//h1[@itemprop="name"]/span/text()')[0]    
    
    

page_href = r'https://play.google.com/store/apps/details?id=com.mojang.minecraftpe&hl=ja'
driver = webdriver.Chrome(executable_path=executable_path,options = options)
driver.get(page_href)
page_text = driver.page_source


full_intro_button = driver.find_elements_by_xpath(r'//div[@class="U26fgb O0WRkf oG5Srb C0oVfc n9lfJ M9Bg4d" and @aria-label="もっと見る"]')
full_intro_button[0].click()

game_name = driver.find_element_by_xpath(r'//h1[@itemprop="name"]/span').text

intro_text = driver.find_elements_by_xpath(r'//div[@jsname="sngebd"]')[0].text               #introduction

num_of_people = driver.find_elements_by_xpath(r'//c-wiz[@jsrenderer="GxnCG"]')[0].text.replace(',','')  #usernumber

tree = etree.HTML(driver.page_source)
stars = tree.xpath(r'//c-wiz[@jsrenderer="GxnCG"]//div[contains(@aria-label,"平均評価:")]/@aria-label')

stars = re.search(r'\d.\d',stars[0]).group()                            #stars
    
[developer,typeofgame] = tree.xpath(r'//span[@class="T32cc UAO9ie"]/a')


developer = developer.text                              #developer and game type
typeofgame = typeofgame.text

price = tree.xpath(r'//button[@class=" LkLjZd ScJHi HPiPcc IfEcue"]/@aria-label')[0]
if price == 'インストール':
    price = 0
else:
    price = re.search(r'\d{1,}',price).group() 

review_href = page_href+r'&showAllReviews=true'
driver.get(review_href)

for i in range(5):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

js_top = "var q=document.documentElement.scrollTop=0"

for j in range(5):
    full_review_text_button = driver.find_elements_by_xpath(r'//button[@class="LkLjZd ScJHi OzU4dc"]')
    try:
        for i in range(len(full_review_text_button)):
            driver.execute_script(js_top)
            full_review_text_button[i].click()
            time.sleep(0.1)
    except:
        break
    
tree = etree.HTML(driver.page_source)

review_block = tree.xpath(r'//div[@class="d15Mdf bAhLNe"]')

all_review = []
for i in range(len(review_block)):
    blocks = copy.deepcopy(review_block[i])
    score = blocks.xpath(r'//div[@role="img"]/@aria-label')
    score = re.search(r'\d/\d',score[0]).group()  
    useful = blocks.xpath(r'//div[@class="jUL89d y92BAb"]')[0].text
    review_text = blocks.xpath(r'//span[@jsname="bN97Pc"]')[0].text
    all_review.append([score,useful,review_text])









'''
        


