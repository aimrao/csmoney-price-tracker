import requests
import os
import json
import sys
import logging
from datetime import datetime, date
from urllib.parse import quote
from dotenv import load_dotenv
from discord_webhook import DiscordWebhook
import cloudscraper

load_dotenv()   # load env file

# initializing env vars from .env file
api = os.environ.get('api_key')
discord_url = os.environ.get('discord_url')
data_dir = os.environ.get('data_dir')
queries = os.environ.get('queries')

# set logging level and format
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_discord(discord_url, message):
    '''Send message to discord webhook'''
    webhook = DiscordWebhook(url=discord_url, content=message)
    response = webhook.execute()
    if response.status_code == 200:
        logging.info("Successfully sent to discord.")
    else:
        logging.error("Failed to send to Discord.")

def get_inr_to_usd_rate():
    '''Read and return the INR->USD conversion rate from file'''
    try:
        with open('{}/inr_to_usd_rate'.format(data_dir),'r') as f:
            file_data = f.readline().split(':')
            if datetime.strptime(file_data[0], "%Y-%m-%d").date() >= date.today():
                return float(file_data[1])
    except Exception as e:
        logging.error(str(e))
        return None

def cache_inr_to_usd_rate(rate):
    '''Cache the INR->USD conversion rate to file with ttl of a day'''
    with open('{}/inr_to_usd_rate'.format(data_dir),'w') as f:
        f.write("{}:{}".format(date.today(),rate))
    return 1

def inr_to_usd(amount):
    '''Get INR->USD conversion rate from fixer.io and cache it if not available in file or stale'''
    if get_inr_to_usd_rate() == None:
        response = json.loads(requests.get("http://data.fixer.io/api/latest?access_key={}&symbols=USD,INR".format(api, amount)).content)
        inr_to_usd_rate = response['rates']['USD']/response['rates']['INR']
        cache_inr_to_usd_rate(inr_to_usd_rate)
    else:
        inr_to_usd_rate = get_inr_to_usd_rate()
    return round_float(inr_to_usd_rate*amount)

def round_float(num):
    '''Round the float value to 4 digits'''
    return round(float(num), 4)

def prettify(data):
    '''Prettify the input dictionary'''
    result = ""
    keys = list(data.keys())
    keys.remove('id')
    for key in keys:
        result += "{}\n".format(data[key])
    return result

def cache_item(item):
    '''Cache the scraped item to file'''
    with open('{}/data'.format(data_dir),'a') as f:
        f.write(json.dumps(item))
        f.write('\n')
    return 0

def check_cache(item):
    '''Check whether item is already present in the data file i.e. if it has been already scraped and sent to discord.'''
    try:
        with open('{}/data'.format(data_dir), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if json.loads(line)['id'] == item['id']:
                    return 1
    except Exception as e:
        logging.error(str(e))
        cache_item(item=item)
        return 0

def csmoney_parser(raw_data):
    '''Parse the item list response from csmoney'''
    items = []
    for item in raw_data['items']:
        data = {}
        data['id'] = item['id']
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
    '''Get item list from csmoney endpoint'''
    url = "https://cs.money/1.0/market/sell-orders?limit=60&maxFloat={}&maxPrice={}&name={}".format(max_float, max_price, quote(name))
    for quality in wear:
        url += "&quality={}".format(quality)
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url, timeout=15)
    if response.status_code == 200:
        raw_data = json.loads(response.content)
        return csmoney_parser(raw_data=raw_data)
    else:
        logging.error(response.status_code)
        return []

def main():
    '''Run the csmoney scraper function for each query in env file'''
    for query in json.loads(queries):
        for item in csmoney_scraper(name=query[0], max_float=query[1], max_price=inr_to_usd(amount=query[2]), wear=query[3]):
            if not check_cache(item=item):
                cache_item(item=item)
                send_discord(discord_url=discord_url, message=prettify(item))
