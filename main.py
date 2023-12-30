import requests
import os
import json
from datetime import datetime, date
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()   # initializing env vars from .env file
api = os.environ.get('api_key')

def get_inr_to_usd_rate():
    try:
        with open('inr_to_usd_rate','r') as f:
            file_data = f.readline().split(':')
            if datetime.strptime(file_data[0], "%Y-%m-%d").date() >= date.today():
                return float(file_data[1])
    except:
        return None

def cache_inr_to_usd_rate(rate):
    with open('inr_to_usd_rate','w') as f:
        f.write("{}:{}".format(date.today(),rate))
    return 1

def inr_to_usd(amount):
    if get_inr_to_usd_rate() == None:
        response = json.loads(requests.get("http://data.fixer.io/api/latest?access_key={}&symbols=USD,INR".format(api, amount)).content)
        inr_to_usd_rate = response['rates']['USD']/response['rates']['INR']
        cache_inr_to_usd_rate(inr_to_usd_rate)
    else:
        inr_to_usd_rate = get_inr_to_usd_rate()
    return round_float(inr_to_usd_rate*amount)

def round_float(num):
    return round(float(num), 4)

def csmoney_parser(raw_data):
    items = []
    for item in raw_data['items']:
        data = {}
        data['name'] = item['asset']['names']['full']
        data['float'] = round_float(item['asset']['float'])
        data['price'] = "{} INR".format(int(item['pricing']['computed']/inr_to_usd(1)))
        data['seller'] = "https://steamcommunity.com/profiles/" + item['seller']['steamId64']
        
        if item['seller']['delivery']['medianTime'] and item['seller']['delivery']['successRate']:
            data['delivery'] = ["{} mins".format(item['seller']['delivery']['medianTime']), "{} %".format(item['seller']['delivery']['successRate'])]
        if item['stickers']:
            data['stickers'] = list({sticker['name']:"{} INR".format(int(sticker['pricing']['default']/inr_to_usd(1)))} for sticker in item['stickers'] if sticker)

        items.append(data)
    return items

def csmoney_scraper(name, max_float, max_price, wear ):
    url = "https://cs.money/1.0/market/sell-orders?limit=60&maxFloat={}&maxPrice={}&name={}&quality={}".format(max_float, max_price, quote(name), wear)
    response = requests.get(url=url)
    if response.status_code == 200:
        raw_data = json.loads(response.content)
        return csmoney_parser(raw_data=raw_data)
    else:
        print(response.status_code)
        return

for item in csmoney_scraper(name="AK-47 Bloodsport", max_float=0.2, max_price=inr_to_usd(amount=7000), wear="ft"):
    print(item)