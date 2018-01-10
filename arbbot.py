#!/usr/bin/env python

import bitgrail
import bitgrail_mimic
import ConfigParser
from ConfigParser import SafeConfigParser
from kucoin.client import Client # as kucoin_client
import pprint
from arbanalysis import ArbAnalysis
import csv
import datetime

Config = ConfigParser.ConfigParser()
Config.read("./.settings.ini")


pp = pprint.PrettyPrinter(indent=4)

BitGrail_ApiKey = Config.get("BitGrail",'ApiKey')
BitGrail_Secret = Config.get("BitGrail",'Secret')
KuCoin_ApiKey = Config.get("KuCoin",'ApiKey')
KuCoin_Secret = Config.get("KuCoin",'Secret')
min_perc_profit = {'KC': float(Config.get("KuCoin",'buy_at_min_perc_profit')), 'BG': float(Config.get("BitGrail",'buy_at_min_perc_profit'))}
trading_enabled = float(Config.getboolean("general",'trading_enabled'))

aa = ArbAnalysis()

BTCUSD = 17000

def main():
	coin = Config.get("general",'coin')
	maxNow = getTradeMaxNow(coin)

	# print("Connecting to Bitgrail. Using key: " + BitGrail_ApiKey + "...")
	bg = bitgrail.Bitgrail(BitGrail_ApiKey,BitGrail_Secret)
	bgm = bitgrail_mimic.Bitgrail_mimic()
	if(bgm.checkWithdrawals('xrb')):
		print "Withdrawals are open."
	else:
		print "Withdrawals under maintenance."
	balance = bgm.getBalance('BTC-XRB')
	print "BitGrail balances:",balance
	# bg.setAuth(BitGrail_ApiKey,BitGrail_Secret)
	ticker = bg.get("ticker","BTC-XRB")
	tBG = {}
	tBG['sell'] = float(ticker['ask'])
	tBG['buy'] = float(ticker['bid'])
	# pp.pprint(ticker)
	# asks, bids = bg.getOrderBook("BTC-XRB")
	# print("========= asks =======")
	# pp.pprint(asks)
	# print("========= bids =======")
	# pp.pprint(bids)

	# print("Connecting to KuCoin. Using key: " + KuCoin_ApiKey + "...")
	# pp.pprint(ticker)
	print("========== ==========")
	spread = 100 * round((tBG['sell'] - tBG['buy'])/tBG['buy'],2)
	print("BitGrail  sell: "+str(tBG['sell'])+"")
	print("BitGrail   buy: "+str(tBG['buy'])+" (spread: "+str(spread)+"%)")
	kc_client = Client(KuCoin_ApiKey, KuCoin_Secret)
	# depth = client.get_order_book('XRB-BTC', limit=20)
	ticker = kc_client.get_tick("XRB-BTC")
	tKC = {}
	tKC['sell'] = float(ticker['sell'])
	tKC['buy'] = float(ticker['buy'])
	spread = 100 * round((tKC['sell'] - tKC['buy'])/tKC['buy'],2)
	print("KuCoin     buy: "+str(tKC['buy'])+" ")
	print("KuCoin    sell: "+str(tKC['sell'])+" (spread: "+str(spread)+"%)")
	print("========== ==========")

	# Buy on KuCoin, sell on BitGrail
	profit_BTC = tBG['buy'] - tKC['sell']
	profit1 = profit_BTC/tKC['sell']*100
	profit1 -= 0.2 + 0.1 # remove fees
	margin = profit1 - min_perc_profit['KC']
	traded, traded_amount, conclusion = (False, 0.0, "NO_ACTION")
	if(profit1 >= min_perc_profit['KC']):
		profit = profit1
		conclusion = "KC->BG"
		print("On KuCoin you can buy "+coin+" for "+str(tKC['sell'])+" which sells for "+str(tBG['buy'])+" on BitGrail ("+str(round(profit1,2))+"% profit).")
		print("On KuCoin you can buy "+coin+" for $"+str(tKC['sell']*BTCUSD)+" which sells for $"+str(tBG['buy']*BTCUSD)+" on BitGrail ("+str(round(profit1,2))+"% profit).")

		if(maxNow > 0) and trading_enabled:
			maxLeftTotal = getTradeLeftTotal(coin)
			print("Most I can trade now is: "+str(maxNow)+" "+coin+" of "+str(maxLeftTotal)+" total.")
			if(Config.getboolean("KuCoin",'disable_buy')):
				print("Not allowed to buy from KuCoin. Skipping trade.")
				exit()
			if(Config.getboolean("BitGrail",'disable_sell')):
				print("Not allowed to sell to BitGrail. Skipping trade.")
				exit()
			maxNow = tradeCap(margin,maxNow)
			# Update limits (whatever happens next)
			updateLimits(coin,maxNow)
			# Get buy price on market A (KC)
			buyAt = tKC['sell']*1.01 # asking price to get it at instantly
			# TODO: check order book if enough is actually available at that price!
			# Get selling price on market B (BG)
			sellAt = tBG['buy']*0.99 # price people already want to buy it at
			# Place order on market A (KC)
			print("kc_client.create_buy_order('XRB-BTC', "+str(buyAt)+", "+str(maxNow)+")")
			traded = True
			traded_amount = maxNow
			buy_order_result = kc_client.create_buy_order('XRB-BTC', str(buyAt), str(maxNow))
			if('orderOid' in buy_order_result):
				print "Order placed: "+buy_order_result['orderOid']
			else:
				print "Order on KC probably wasnt placed! Server response: "
				pp.pprint(buy_order_result)
				updateLimits(coin,0,abortReason="KC order placement failed.")
				quit("Dude, fix me! I guess I'll be nice and not sell your coins on the the other exchange.")

			# Place order on market B (BG)
			print("Creating sell order on BitGrail of "+str(maxNow)+" "+coin+" at "+str(sellAt))

			balance = bgm.getBalance()
			if(balance['XRB'] < maxNow):
				print "Whoa... I'm not going to short. I almost tried to sell "+str(maxNow)+" but I have a balance of "+str(balance['XRB'])+" on BitGrail. Capping to that."
				maxNow = min(maxNow,balance['XRB'])
			result = bgm.createOrder('BTC-XRB','sell',maxNow,sellAt)
			print("BG result:",result)
		else:
			print("Not allowed to trade anymore!")
	else:
		print("Profit (KC->BG) too low: "+str(round(profit1,2))+"% < "+str(min_perc_profit['KC'])+"%")

	# Buy on BitGrail, sell on KuCoin
	profit_BTC = tKC['buy'] - tBG['sell']
	profit2 = profit_BTC/tBG['sell']*100
	profit2 -= 0.2 + 0.1 # remove fees
	margin = profit2 - min_perc_profit['BG']
	if(profit2 >= min_perc_profit['BG']):
		conclusion = "BitGrail is CHEAPER!"
		print("On BitGrail you can buy "+coin+" for "+str(tBG['sell'])+" which sells for "+str(tKC['buy'])+" on KuCoin ("+str(round(profit2,2))+"% profit).")
		print("On BitGrail you can buy "+coin+" for $"+str(tBG['sell']*BTCUSD)+" which sells for $"+str(tKC['buy']*BTCUSD)+" on KuCoin ("+str(round(profit2,2))+"% profit).")
		if(maxNow > 0) and trading_enabled:
			maxLeftTotal = getTradeLeftTotal(coin)
			print("Most I can trade now is: "+str(maxNow)+" "+coin+" of "+str(maxLeftTotal)+" total.")
			if(Config.getboolean("BitGrail",'disable_buy')):
				print("Not allowed to buy from BitGrail. Skipping trade.")
				exit()
			if(Config.getboolean("KuCoin",'disable_sell')):
				print("Not allowed to sell to KuCoin. Skipping trade.")
				exit()
			maxNow = tradeCap(margin,maxNow)
			# Update limits (whatever happens next)
			updateLimits(coin,maxNow)
			# Get buy price on market A (BG)
			buyAt = tBG['sell']*1.01 # asking price to get it at instantly
			# TODO: check order book if enough is actually available at that price!
			# Get selling price on market B (KC)
			sellAt = tKC['buy']*0.99 # price people already want to buy it at
			# Place buy order on market A (BG)
			traded = True
			traded_amount = -maxNow
			print("BitGrail: creating buy order of "+str(maxNow)+" "+coin+" at "+str(buyAt)+".")
			bg_balance = bgm.getBalance()
			if(bg_balance['BTC'] < maxNow * buyAt):
				print "Crap. I ran out of BTC on the exchange... Want to buy: "+str(maxNow)+" but I have a balance of "+str(bg_balance['BTC'])+" on BitGrail."
				print("\nI N S E R T   C O I N\n")
				quit("I'll stop purchasing now.")
			result = bgm.createOrder('BTC-XRB','buy',maxNow,buyAt)
			print("BG result:",result)

			# Place sell order on market B (KC)
			print("kc_client.create_sell_order('XRB-BTC', "+str(sellAt)+", "+str(maxNow)+")")
			sell_order_result = kc_client.create_sell_order('XRB-BTC', str(sellAt), str(maxNow))
			# {   u'orderOid': u'5a54f203de88b3646e127e2f'}
			if('orderOid' in sell_order_result):
				print "Order placed: "+sell_order_result['orderOid']
			else:
				print "Order probably wasnt placed! Server response: "
				updateLimits(coin,0,abortReason="KC sell order placement failed?")
				pp.pprint(sell_order_result)

		else:
			print("Not allowed to trade anymore!")
	else:
		print("Profit (BG->KC) too low: "+str(round(profit2,2))+"% < "+str(min_perc_profit['BG'])+"%")
	# fake a trade
	# get list of active orders
	# result = bg.post('lasttrades')
	# pp.pprint(result)
	if traded == True:
		print("Orders on KuCoin:")
		# FIXME
		# orders = kc_client.get_active_orders('XRM-BTC')
		# pp.pprint(orders)

	dt = datetime.datetime.now().isoformat()
	# time,bitgrail_sell,bitgrail_buy,kcoin_sell,kcoin_buy,profitKC2BG,profitBG2KC
	logCSV([dt,tBG['sell'],tBG['buy'],tKC['sell'],tKC['buy'],str(round(profit1,2))+"%",str(round(profit2,2))+"%",traded_amount])
# sold 57 XRB on KuCoin for 0.00189998
# could by at 0.00184995
# KuCoin deposit addr: xrb_3gywx85jgzyxtd44wh69m3inzijsbyw3ozdzmwzozbcqro5ktkm53d8dz583
def tradeCap(margin,maxNow):
	if(margin <= 1):
		maxNow = min(4+round(margin*4),maxNow)
		print("Capped order to "+str(maxNow)+" (profit margin only "+str(round(margin,2))+"% above minimum)")
		return maxNow
	return maxNow

def logCSV(vars):
	with open('log.csv','a') as f:
		writer = csv.writer(f, delimiter='\t')
		writer.writerow(vars)

def getTradeMaxNow(coin):
	TradeLimits = ConfigParser.ConfigParser()
	TradeLimits.read('./trade_allowed.ini')
	return min(float(TradeLimits.get(coin,'max_qty_left')),float(TradeLimits.get(coin,'max_per_trade')))

def getTradeLeftTotal(coin):
	TradeLimits = ConfigParser.ConfigParser()
	TradeLimits.read('./trade_allowed.ini')
	if(TradeLimits.get(coin,'self_abort') != 'False'):
		quit("Aborting trading. Reason: " + TradeLimits.get(coin,'self_abort'))
	return float(TradeLimits.get(coin,'max_qty_left'))

def updateLimits(coin,decreaseLimits,abortReason=None):
	parser = SafeConfigParser()
	parser.read('./trade_allowed.ini')
	ml = float(parser.get(coin, 'max_qty_left'))
	if(ml < 0):
		print("Somethings VERY WRONG. max_qty_left shouldn't be negative. Ever.")
	if((ml-decreaseLimits)<0):
		print("Somethings VERY WRONG. Exceeded trade limit?!")
	if(abortReason):
		parser.set(coin,'self_abort',abortReason)
	parser.set(coin,'max_qty_left',str(ml-decreaseLimits))
	with open('./trade_allowed.ini', 'wb') as configfile:
		parser.write(configfile)


if __name__ == "__main__":
    main()


# OLDER STUFF


	# orderbook = bg.get("orderbook","BTC-XRB")
	# aa.parse_orders(orderbook)
