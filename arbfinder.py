#!/usr/bin/env python
# -*- coding: utf-8 -*-

from kucoin.client import Client as KcClient # as kucoin_client
from binance.client import Client as BiClient
import ConfigParser
import pprint

import csv
import datetime

def logCSV(vars):
	with open(logFile,'a') as f:
		writer = csv.writer(f, delimiter='\t')
		writer.writerow(vars)

dt = datetime.datetime.now().isoformat()


pp = pprint.PrettyPrinter(indent=4)

Config = ConfigParser.ConfigParser()
Config.read("./.settings.ini")

KuCoin_ApiKey = Config.get("KuCoin",'ApiKey')
KuCoin_Secret = Config.get("KuCoin",'Secret')
Binance_ApiKey = Config.get("Binance",'ApiKey')
Binance_Secret = Config.get("Binance",'Secret')

logFile = 'arbfinder.csv'

exchanges = { 
	'KC': {'name': 'KuCoin'}, 
	'BI': {'name': 'Binance'}
}
client = {}
client['KC'] = KcClient(KuCoin_ApiKey, KuCoin_Secret)
client['BI'] = BiClient(Binance_ApiKey, Binance_Secret)

prices = {}
prices_tmp = {}
prices['KC'] = {}
prices['BI'] = {}

# get all symbol prices
# Ex1 = 'BI'
prices_tmp['BI'] = client['BI'].get_all_tickers()
for price in prices_tmp['BI']:
	p = float(price['price'])
	symbol = price['symbol']
	prices['BI'][symbol] = { 'price': p }

coins = client['KC'].get_trading_symbols()
# pp.pprint(coins)
for coin in coins:
	# print coin
	if('lastDealPrice' in coin):
		p = coin['lastDealPrice']
		symbol = coin['symbol'].replace('-','')
		if(coin['coinTypePair'] in ['BTC']):
			print "yes: "+ str(coin)
			volUSD = coin['volValue']*13000
			print symbol + " volume: " + str(volUSD)
		if(coin['coinTypePair'] in ['ETH']):
			volUSD = coin['volValue']*1200
			print symbol + "volume: " + str(volUSD)
		if(volUSD > 500000):
			# print "yes: "+ str(coin)
			prices['KC'][symbol] = { 'price': p}
		else:
			print "Insufficient."
	# else:
		# print "no:  "+ str(coin)

for symbol in prices['BI']:
	p = {}
	p['BI'] = prices['BI'][symbol]['price']
	perc_diff = None
	if(symbol in prices['KC']):
		p['KC'] = prices['KC'][symbol]['price']
		perc_diff = round((p['KC'] / p['BI'] * 100 - 100),1)
	else:
		p['KC'] = -1.0
	if(perc_diff != None):
		 logMe = [dt,symbol,p['BI'],p['KC'],perc_diff]
		 print logMe
		 logCSV(logMe)



# COINBASECOIN price_delta
