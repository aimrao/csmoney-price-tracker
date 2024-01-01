# csmoney price tracker

Track price of a particular item/items and alert on discord.

## Dependency
- fixer.io api key required to get price conversion rates
> Note: If you do not want to use the api access key, manually add the 1 INR to 1 USD price rate in the `inr_to_usd_rate` file with date far from today.

## ENV File
Add the following details in .env file:
- api_key - your fixer.io api key
- discord_url - discord webhook url
- data_dir - full path to the dir where to cache the currency conversion rate and item list file
- queries - query containing item to be scraped details in the following format 
`queries=[item1, item2, item3,...]` where item1..n is another list in the format `[item_full_name, max_float, max_price, list containing wears]`

e.g,
```python
queries=[["AK-47 Bloodsport",0.2,7200,["ft", "mw"]], ["AK-47 Bloodsport",0.2,8100,["fn"]]] 
```
## Usage
Build the dockerfile and run it using the following command:
```sh
sudo docker build -t csmoney-price-tracker .
sudo docker run -d --name csmoney-price-tracker --env-file ./path_to_env/.env -v path_to_data_dir/:/data_dir --log-opt max-size=10m --log-opt max-file=3 csmoney-price-tracker
```
Or, 
use the prebuilt image:
```sh
sudo docker run -d --name csmoney-price-tracker --env-file ./path_to_env/.env -v path_to_data_dir/:/data_dir --log-opt max-size=10m --log-opt max-file=3 aimrao/csmoney-price-tracker
```
