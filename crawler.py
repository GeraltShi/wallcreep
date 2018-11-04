import requests
import urllib.request
from bs4 import BeautifulSoup
import os
import time

head = 'https://wallpapersite.com'
url = 'https://wallpapersite.com/?page=1'
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')
items = soup.select("div.pics > p > a")
folder_path = './downloads/'
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

print(len(items))

for index, item in enumerate(items):
    if item:
        html = head + item.get('href')
        sub_response = requests.get(html, headers=headers)
        sub_soup = BeautifulSoup(sub_response.content, 'html.parser')
        sub_items = sub_soup.select("div.pic-left > div > span.res-ttl > a.original")
        sub_img = head + sub_items[0].get('href')
        img_name = folder_path + sub_img.strip().split('/')[-1]
        with open(img_name, 'wb') as file:
            file.write(requests.get(sub_img).content)
            file.flush()
        file.close()
        print('%d images downloaded' % (index + 1))
