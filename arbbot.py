#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bitgrail
import bitgrail_mimic
import ConfigParser
from ConfigParser import SafeConfigParser
from kucoin.client import Client # as kucoin_client
import pprint
from arbanalysis import ArbAnalysis
import csv
import datetime
from modules.Telegram import Telegram
import socket


Config = ConfigParser.ConfigParser()
Config.read("./.settings.ini")

dt = datetime.datetime.now().isoformat()

pp = pprint.PrettyPrinter(indent=4)

logFilePrefix = Config.get("general",'logFilePrefix')
instanceName = Config.get("general",'instance_name')

BitGrail_ApiKey = Config.get("BitGrail",'ApiKey')
BitGrail_Secret = Config.get("BitGrail",'Secret')
KuCoin_ApiKey = Config.get("KuCoin",'ApiKey')
KuCoin_Secret = Config.get("KuCoin",'Secret')
min_perc_profit = {'KC': float(Config.get("KuCoin",'buy_at_min_perc_profit')), 'BG': float(Config.get("BitGrail",'buy_at_min_perc_profit'))}
trading_enabled = float(Config.getboolean("general",'trading_enabled'))
starting_balance_btc = float(Config.get("general",'starting_balance_btc'))

T_BOT_ID = Config.get("Telegram",'telegram_bot_id')
T_CHAT_ID = Config.get("Telegram",'telegram_chat_id')
telegramBot = Telegram(T_BOT_ID)
telegramBot.set_chat_id(T_CHAT_ID)

symbol = Config.get("general",'symbol').upper()
symbol_base = Config.get("general",'symbol_base').upper()

BTCEUR = 11328

def getIp():
    return str([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), 
s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, 
socket.SOCK_DGRAM)]][0][1]]) if l][0][0])

graphURL = "http://"+ getIp() + ":"+Config.get("webserver",'webServerPort')+"/"

def compareCheapness(ex1,ex2):
	ex1_name, ex1_sell, ex1_buy = ex1
	ex2_name, ex2_sell, ex2_buy = ex2
	if((ex1_sell + ex1_buy) - (ex2_sell + ex2_buy)):
		p = str(round((ex2_sell - ex1_buy)/ex2_sell*100,1)) + '%'
		exchange1_cheaper = True
		s1 = ex1_name+" is currently cheaper than "+str(ex2_name)
		s2 = ex1_name+" (Sell: "+str(ex1_sell)+") is currently "+p+" cheaper than "+str(ex2_name)+" (Sell: "+str(ex2_sell)+")"
	else:
		p = str(round((ex1_sell - ex2_buy)/ex1_sell*100,1)) + '%'
		s1 = ex2_name+" is currently cheaper than "+str(ex1_name)
		s2 = ex2_name+" (Sell: "+str(ex2_sell)+") is currently "+p+" cheaper than "+str(ex1_name)+" (Sell: "+str(ex1_sell)+")"
	print(s2)
	return s1, s2

def main():
	print("========== ArbBot - "+ symbol + '-' + symbol_base + ' ' + instanceName +" ========== "+str(dt))
	maxNow = getTradeMaxNow(symbol)

	bg = bitgrail.Bitgrail(BitGrail_ApiKey,BitGrail_Secret)
	kc_client = Client(KuCoin_ApiKey, KuCoin_Secret)
	bgm = bitgrail_mimic.Bitgrail_mimic()
	bgm.set_coin(symbol=symbol,symbol_base=symbol_base)

	if(Config.getboolean("BitGrail",'checkWithdrawals')):
		if(bgm.checkWithdrawals(symbol)):
			print "BitGrail "+symbol+" withdrawals are open."
			telegramBot.text_message(symbol+" withdrawals just opened up on BitGrail!",topic="Mon.BG."+symbol+"_Withdrawals")
		else:
			print "BitGrail "+symbol+" withdrawals under maintenance."
			telegramBot.text_message(symbol+" withdrawals just became deactivated again! (under maintenance)",topic="Mon.BG."+symbol+"_Withdrawals")
	bg_balance = bgm.getBalance()
	print "bgm.getBalance("+symbol_base+'-'+symbol+",symbol="+symbol+", symbol_base="+symbol_base+"): "
	# bg.setAuth(BitGrail_ApiKey,BitGrail_Secret)
	ticker = bg.get("ticker",symbol_base+'-'+symbol)
	tBG = {'sell': float(ticker['ask']), 'buy': float(ticker['bid'])}

	print("========== Prices ==========")
	spread = 100 * round((tBG['sell'] - tBG['buy'])/tBG['buy'],2)
	print("BitGrail  sell: "+str(tBG['sell'])+"")
	print("BitGrail   buy: "+str(tBG['buy'])+" (spread: "+str(spread)+"%)")

	ticker = kc_client.get_tick(symbol+'-'+symbol_base)
	# pp.pprint(ticker)
	tKC = {}
	tKC['sell'] = float(ticker['sell'])
	tKC['buy'] = float(ticker['buy'])
	spread = 100 * round((tKC['sell'] - tKC['buy'])/tKC['buy'],2)
	print("KuCoin     buy: "+str(tKC['buy'])+" ")
	print("KuCoin    sell: "+str(tKC['sell'])+" (spread: "+str(spread)+"%)")
	print("\n========== Balances ==========")

	# Balances
	balanceStr = ''
	if(symbol in bg_balance):
		coinValueBaseCurrency = bg_balance[symbol] * float(ticker['lastDealPrice'])
		total_in_BaseCurrency = coinValueBaseCurrency+bg_balance[symbol_base]
		balanceStr = "BitGrail: "+str(round(bg_balance[symbol_base],5))+" "+symbol_base+" + "+str(round(bg_balance[symbol],5))+" "+symbol+" = "+str(round(total_in_BaseCurrency,5))+" "+symbol_base+"\n"
	balances = kc_client.get_all_balances()
	kc_balance = {}
	for balance in balances:
		if(balance['coinType'] == symbol_base):
			kc_balance[symbol_base] = balance['balance']
		if(balance['coinType'] == symbol):
			if(balance['balance'] == False): balance['balance'] = 0.0
			kc_balance[symbol] = balance['balance']
	if(symbol in kc_balance):
		coinValueBaseCurrency2 = kc_balance[symbol] * float(ticker['lastDealPrice'])
		total_in_BaseCurrency2 = coinValueBaseCurrency2+kc_balance[symbol_base]
		balanceStr = balanceStr + "KuCoin: "+str(round(kc_balance[symbol_base],5))+" "+symbol_base+" + "+str(round(kc_balance[symbol],5))+" "+symbol+" = "+str(round(total_in_BaseCurrency2,5))+" "+symbol_base+"\n"
	balanceStr = balanceStr + "Grand total: "+str(round(bg_balance[symbol_base]+kc_balance[symbol_base],5))+" "+symbol_base+" + "+str(round(bg_balance[symbol]+kc_balance[symbol],5))+" "+symbol+" = "+str(round(total_in_BaseCurrency+total_in_BaseCurrency2,5))+" "+symbol_base+"\n"

	btc_gains = bg_balance[symbol_base]+kc_balance[symbol_base]-starting_balance_btc
	balanceStr = balanceStr + symbol_base+" gains: "+str(round(btc_gains,5))+" "+symbol_base+" (about € "+str(round(btc_gains*BTCEUR,2))+")\n"
	print balanceStr

	print("\n========== Trade ==========")
	# cheapness_punchline, cheapness_details = compareCheapness(('BitGrail',tBG['sell'],tBG['buy']),('KuCoin',tKC['sell'],tKC['buy']))
	# telegramBot.text_message(cheapness_punchline,topic="Mon.Cheapness",msg_full=cheapness_details)
	# Buy on KuCoin, sell on BitGrail
	profit_BaseSymbol = tBG['buy'] - tKC['sell']
	profit1 = profit_BaseSymbol/tKC['sell']*100
	profit1 -= 0.2 + 0.1 # remove fees
	margin = profit1 - min_perc_profit['KC']
	traded, traded_amount, conclusion = (False, 0.0, "NO_ACTION")
	if(profit1 >= min_perc_profit['KC']):
		profit = profit1
		conclusion = "KC->BG"
		print("On KuCoin you can buy "+symbol+" for "+str(tKC['sell'])+" which sells for "+str(tBG['buy'])+" on BitGrail ("+str(round(profit1,2))+"% profit).")
		print("On KuCoin you can buy "+symbol+" for € "+str(tKC['sell']*BTCEUR)+" which sells for €"+str(tBG['buy']*BTCEUR)+" on BitGrail ("+str(round(profit1,2))+"% profit).")

		maxNow = tradeCap(margin,maxNow,availableForSale = bg_balance[symbol])
		if(maxNow > 0.1) and trading_enabled:
			maxLeftTotal = getTradeLeftTotal(symbol)
			print("Most I can trade now is: "+str(maxNow)+" "+symbol+" of "+str(maxLeftTotal)+" total.")
			if(Config.getboolean("KuCoin",'disable_buy')):
				print("Not allowed to buy from KuCoin. Skipping trade.")
				exit()
			if(Config.getboolean("BitGrail",'disable_sell')):
				print("Not allowed to sell to BitGrail. Skipping trade.")
				exit()
			# Update limits (whatever happens next)
			updateLimits(symbol,maxNow)
			# Get buy price on market A (KC)
			buyAt = tKC['sell']*1.02 # asking price to get it at instantly

			# TODO: check order book if enough is actually available at that price!
			# Get selling price on market B (BG)
			sellAt = tBG['buy']*0.98 # price people already want to buy it at
			# Place order on market A (KC)
			print("kc_client.create_buy_order("+symbol+'-'+symbol_base+", "+str(buyAt)+", "+str(maxNow)+")")
			traded = True
			traded_amount = maxNow
			s = "Buying "+str(maxNow)+" "+symbol+" on KuCoin at "+str(buyAt) + ": "
			buy_order_result = kc_client.create_buy_order(symbol+'-'+symbol_base, str(buyAt), str(maxNow))
			if('orderOid' in buy_order_result):
				print "Order placed: "+buy_order_result['orderOid']
				s = s + "Order placed.\n"
			else:
				print "Order on KC probably wasnt placed! Server response: "
				pp.pprint(buy_order_result)
				err = "KC order placement failed."
				updateLimits(symbol,0,abortReason=err)
				telegramBot.text_message(s + balanceStr + err)
				quit("Dude, fix me! I guess I'll be nice and not sell your coins on the the other exchange.")

			# Place order on market B (BG)
			print("Creating sell order on BitGrail of "+str(maxNow)+" "+symbol+" at "+str(sellAt))

			balance = bgm.getBalance()
			if(balance[symbol] < maxNow):
				warning = "Whoa... I'm not going to short "+symbol+". I almost tried to sell "+str(maxNow)+" but I have a balance of "+str(balance[symbol])+" on BitGrail. Capping to that."
				s = s + warning
				print warning
				maxNow = min(maxNow,balance[symbol])
			result = bgm.createOrder(symbol_base+'-'+symbol,'sell',maxNow,sellAt)
			print("BG result:",result)
			s = s + "\nBitGrail sell order of "+str(maxNow)+" "+symbol+" placed at "+str(sellAt)+" "+symbol_base+". "
			s = s + "\nProfit "+str(round(profit1,1))+"% >= "+str(min_perc_profit['KC'])+"%.\n"
			s = s + balanceStr
			s = s + "Result: " + str(result)
			telegramBot.text_message(s + "\n" + graphURL)
		else:
			print("Not allowed to trade anymore!")
	else:
		print("KC->BG profit below "+str(min_perc_profit['KC'])+"%:\t"+str(round(profit1,2))+"%")

	# Buy on BitGrail, sell on KuCoin
	profit_BaseSymbol = tKC['buy'] - tBG['sell']
	profit2 = profit_BaseSymbol/tBG['sell']*100
	profit2 -= 0.2 + 0.1 # remove fees
	margin = profit2 - min_perc_profit['BG']
	if(profit2 >= min_perc_profit['BG']):
		conclusion = "BitGrail is CHEAPER!"
		print("On BitGrail you can buy "+symbol+" for "+str(tBG['sell'])+" which sells for "+str(tKC['buy'])+" on KuCoin ("+str(round(profit2,2))+"% profit).")
		print("On BitGrail you can buy "+symbol+" for € "+str(tBG['sell']*BTCEUR)+" which sells for € "+str(tKC['buy']*BTCEUR)+" on KuCoin ("+str(round(profit2,2))+"% profit).")
		maxNow = tradeCap(margin,maxNow,availableForSale = kc_balance[symbol])
		if(maxNow > 0.1) and trading_enabled:
			maxLeftTotal = getTradeLeftTotal(symbol)
			print("Most I can trade now is: "+str(maxNow)+" "+symbol+" of "+str(maxLeftTotal)+" total.")
			if(Config.getboolean("BitGrail",'disable_buy')):
				print("Not allowed to buy from BitGrail. Skipping trade.")
				exit()
			if(Config.getboolean("KuCoin",'disable_sell')):
				print("Not allowed to sell to KuCoin. Skipping trade.")
				exit()
			# Update limits (whatever happens next)
			updateLimits(symbol,maxNow)
			# Get buy price on market A (BG)
			buyAt = tBG['sell']*1.02 # asking price to get it at instantly
			# TODO: check order book if enough is actually available at that price!
			# Get selling price on market B (KC)
			sellAt = tKC['buy']*0.98 # price people already want to buy it at
			sellAt = tKC['buy']*1.02 # temporarily don't sell to increase the coin exposure
			# Place buy order on market A (BG)
			traded = True
			traded_amount = -maxNow
			s = "BitGrail: creating buy order of "+str(maxNow)+" "+symbol+" at "+str(buyAt)+"."
			print(s)
			bg_balance = bgm.getBalance()
			if(bg_balance[symbol] < maxNow * buyAt):
				s = s + "Not enough coins.\n"
				print "Crap. I ran out of "+symbol_base+" on the exchange... Want to buy: "+str(maxNow)+" but I have a balance of "+str(bg_balance[symbol_base])+" on BitGrail."
				print("\nI N S E R T   C O I N\n")
				quit("I'll stop purchasing now.")
			result = bgm.createOrder(symbol_base+'-'+symbol,'buy',maxNow,buyAt)
			print("BG result:",result)
			s = s + "\nResult: "+str(result)

			# Place sell order on market B (KC)
			print("kc_client.create_sell_order("+symbol_base+'-'+symbol+", "+str(sellAt)+", "+str(maxNow)+")")
			sell_order_result = kc_client.create_sell_order(symbol+'-'+symbol_base, str(sellAt), str(maxNow))
			# {   u'orderOid': u'5a54f203de88b3646e127e2f'}
			if('orderOid' in sell_order_result):
				s = s + "\nKuCoin sell order of "+str(maxNow)+" "+symbol+" placed at "+str(sellAt)+" "+symbol_base+"."
				s = s + "\nProfit "+str(round(profit2,1))+"% >= "+str(min_perc_profit['BG'])+"%.\n"
				s = s + balanceStr
				print "Order placed: "+sell_order_result['orderOid']
			else:
				print "Order probably wasnt placed! Server response: "
				updateLimits(symbol,0,abortReason="KC sell order placement failed?")
				pp.pprint(sell_order_result)
				s = s + balanceStr
				s = s + "\nFailure: "+str(sell_order_result)

			telegramBot.text_message(s + "\n" + graphURL)
		else:
			print("Not allowed to trade anymore!")
	else:
		print("BG->KC profit below "+str(min_perc_profit['BG'])+"%:\t"+str(round(profit2,2))+"%")

	# time	bitgrail_sell	bitgrail_buy	kcoin_sell	kcoin_buy	profitKC2BG	profitBG2KC	traded
	logCSV([dt,tBG['sell'],tBG['buy'],tKC['sell'],tKC['buy'],str(round(profit1,2))+"%",str(round(profit2,2))+"%",traded_amount])

def tradeCap(margin,maxNow,availableForSale=None):
	if availableForSale < float(Config.get('general','balance_cap')):
		print("Capped order because balance is low: "+str(availableForSale)+" coins. Margin before: "+str(margin))
		margin = margin * (availableForSale / float(Config.get('general','balance_cap')))
		print("Margin after: "+str(margin))
	if(margin <= 1):
		maxNow = min(0+round(margin*4),maxNow)
		print("Capped order to "+str(maxNow)+" (profit margin only "+str(round(margin,2))+"% above minimum)")
		return maxNow
	return maxNow

def logCSV(vars):
	with open(logFilePrefix+'_'+symbol+'-'+symbol_base+'.csv','a') as f:
		writer = csv.writer(f, delimiter='\t')
		writer.writerow(vars)

def getTradeMaxNow(symbol):
	TradeLimits = ConfigParser.ConfigParser()
	TradeLimits.read('./trade_allowed.ini')
	return min(float(TradeLimits.get(symbol,'max_qty_left')),float(TradeLimits.get(symbol,'max_per_trade')))

def getTradeLeftTotal(symbol):
	TradeLimits = ConfigParser.ConfigParser()
	TradeLimits.read('./trade_allowed.ini')
	if(TradeLimits.get(symbol,'self_abort') != 'False'):
		quit("Aborting trading. Reason: " + TradeLimits.get(symbol,'self_abort'))
	return float(TradeLimits.get(symbol,'max_qty_left'))

def updateLimits(symbol,decreaseLimits,abortReason=None):
	parser = SafeConfigParser()
	parser.read('./trade_allowed.ini')
	ml = float(parser.get(symbol, 'max_qty_left'))
	if(ml < 0):
		print("Somethings VERY WRONG. max_qty_left shouldn't be negative. Ever.")
	if((ml-decreaseLimits)<0):
		print("Somethings VERY WRONG. Exceeded trade limit?!")
	if(abortReason):
		parser.set(symbol,'self_abort',abortReason)
	parser.set(symbol,'max_qty_left',str(ml-decreaseLimits))
	with open('./trade_allowed.ini', 'wb') as configfile:
		parser.write(configfile)


if __name__ == "__main__":
    main()


