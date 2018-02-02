#!/usr/bin/env python
# -*- coding: utf-8 -*-

import bitgrail
import bitgrail_mimic
# import ConfigParser
from ConfigParser import SafeConfigParser
from kucoin.client import Client # as kucoin_client
from arbanalysis import ArbAnalysis

from modules.Utils import *
import modules.CoinData as CoinData
import random


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
	print("========== ArbBot - "+ symbol + '-' + symbol_base + ' [' + conf('general.instance_name') +"] ========== "+str(dt))
	actions = checkTelegramMessages()
	maxNow = getTradeMaxNow(symbol)

	bg = bitgrail.Bitgrail(conf('BitGrail.ApiKey'),conf('BitGrail.Secret'))
	kc_client = Client(conf('KuCoin.ApiKey'),conf('KuCoin.Secret'))
	bgm = bitgrail_mimic.Bitgrail_mimic()
	bgm.set_coin(symbol=symbol,symbol_base=symbol_base)

	if(conf('BitGrail.checkWithdrawals','bool')) and (random.randrange(10) > 5):
		if(bgm.checkWithdrawals(symbol)):
			print "BitGrail "+symbol+" withdrawals are open."
			telegramBot.text_message(symbol+" withdrawals just opened up on BitGrail!",topic="Mon.BG."+symbol+"_Withdrawals")
		else:
			print "BitGrail "+symbol+" withdrawals under maintenance."
			telegramBot.text_message(symbol+" withdrawals just became deactivated again! (under maintenance)",topic="Mon.BG."+symbol+"_Withdrawals")
	bg_balance = bgm.getBalance()

	print("\n========== Balances ==========")
	balanceStr = ''
	if(symbol in bg_balance):
		lastDealPrice = float(getConfig('cache','lastDealPrice'))
		coinValueBaseCurrency = bg_balance[symbol] * lastDealPrice
		total_in_BaseCurrency = coinValueBaseCurrency+bg_balance[symbol_base]
		balanceStr =              "BitGrail:    "+str(round(bg_balance[symbol_base],5)).ljust(8)+" "+symbol_base+" + "+str(round(bg_balance[symbol],5)).ljust(8)+" "+symbol+" = "+str(round(total_in_BaseCurrency,5)).ljust(8)+" "+symbol_base+"\n"
	balances = kc_client.get_all_balances()
	kc_balance = {}
	for balance in balances:
		if(balance['coinType'] == symbol_base):
			kc_balance[symbol_base] = balance['balance']
		if(balance['coinType'] == symbol):
			if(balance['balance'] == False): balance['balance'] = 0.0
			kc_balance[symbol] = balance['balance']
	if(symbol in kc_balance):
		coinValueBaseCurrency2 = kc_balance[symbol] * lastDealPrice
		total_in_BaseCurrency2 = coinValueBaseCurrency2+kc_balance[symbol_base]
		balanceStr = balanceStr + "KuCoin:      "+str(round(kc_balance[symbol_base],5)).ljust(8)+" "+symbol_base+" + "+str(round(kc_balance[symbol],5)).ljust(8)+" "+symbol+" = "+str(round(total_in_BaseCurrency2,5)).ljust(8)+" "+symbol_base+"\n"
	balanceStr = balanceStr +     "Grand total: "+str(round(bg_balance[symbol_base]+kc_balance[symbol_base],5)).ljust(8)+" "+symbol_base+" + "+str(round(bg_balance[symbol]+kc_balance[symbol],5)).ljust(8)+" "+symbol+" = "+str(round(total_in_BaseCurrency+total_in_BaseCurrency2,5)).ljust(8)+" "+symbol_base+"\n"

	btc_gains = bg_balance[symbol_base]+kc_balance[symbol_base]
	btc_gains-= conf('general.starting_balance_btc','float')
	coin_gains = bg_balance[symbol]+kc_balance[symbol]
	coin_gains-= float(getConfig(symbol,'starting_balance'))
	drift_max = 1.5 * float(getConfig(symbol,'max_per_trade'))
	if(abs(coin_gains) > drift_max):
		msg = "The amount of coins has drifted by "+str(coin_gains)+" "+symbol
		msg += ". This is more than the allowed "+str(drift_max)+" "+symbol+". "
		telegramBot.text_message(msg,topic = "coin_drift")
		updateLimits(symbol,0,abortReason="CoinDriftedBy"+str(coin_gains)+symbol)
	else:
		telegramBot.text_message("Coin drift acceptable again.",topic = "coin_drift")
	balanceStr = str(balanceStr + symbol_base+" gains: ").ljust(14)+str(round(btc_gains,5)).ljust(8)+" "+symbol_base+" (about € "+str(round(btc_gains*BTCEUR,2))+") + "+str(round(coin_gains,4))+" "+symbol+"\n"
	print balanceStr

	ch_s = "===== BALANCE CHANGE =====\n"
	if(float(getConfig(symbol,'KC_last_balance')) != kc_balance[symbol]):
		ch_s += "KuCoin balance changed from "+getConfig(symbol,'KC_last_balance_base')+" to "+str(kc_balance[symbol_base])+" "+symbol_base + "\n" + balanceStr
		telegramBot.text_message(ch_s)
		print(ch_s + "\n")
	elif(float(getConfig(symbol,'BG_last_balance_base')) != bg_balance[symbol_base]):
		ch_s += "BitGrail balance changed from "+getConfig(symbol,'BG_last_balance_base')+" to "+str(bg_balance[symbol_base])+" "+symbol_base  + "\n" + balanceStr
		telegramBot.text_message(ch_s)
		print(ch_s + "\n")
	elif(float(getConfig(symbol,'KC_last_balance')) != kc_balance[symbol]):
		ch_s += "KuCoin balance changed from "+getConfig(symbol,'KC_last_balance')+" to "+str(kc_balance[symbol])+" "+symbol + "\n" + balanceStr
		telegramBot.text_message(ch_s)
		print(ch_s + "\n")
	elif(float(getConfig(symbol,'BG_last_balance')) != bg_balance[symbol]):
		ch_s += "BitGrail balance changed from "+getConfig(symbol,'BG_last_balance')+" to "+str(bg_balance[symbol])+" "+symbol  + "\n" + balanceStr
		telegramBot.text_message(ch_s)
		print(ch_s + "\n")
	setConfig(symbol,'KC_last_balance_base',kc_balance[symbol_base])
	setConfig(symbol,'BG_last_balance_base',bg_balance[symbol_base])
	setConfig(symbol,'KC_last_balance',kc_balance[symbol])
	setConfig(symbol,'BG_last_balance',bg_balance[symbol])

	ticker = bg.get("ticker",symbol_base+'-'+symbol)
	tBG = {'sell': float(ticker['ask']), 'buy': float(ticker['bid'])}

	ps  = "========== Prices ==========\n"
	spread = 100 * round((tBG['sell'] - tBG['buy'])/tBG['buy'],2)
	ps += "BitGrail  sell: "+str(tBG['sell']).ljust(10)+"\n"
	ps += "BitGrail   buy: "+str(tBG['buy']).ljust(10)+" (spread: "+str(spread)+"%)\n"

	ticker = kc_client.get_tick(symbol+'-'+symbol_base)
	setConfig('cache','lastDealPrice',float(((ticker['lastDealPrice']+tBG['sell']+tBG['buy'])/3)))
	tKC = {}
	tKC['sell'] = float(ticker['sell'])
	tKC['buy'] = float(ticker['buy'])
	spread = 100 * round((tKC['sell'] - tKC['buy'])/tKC['buy'],2)
	ps += "KuCoin     buy: "+str(tKC['buy']).ljust(10)+" \n"
	ps += "KuCoin    sell: "+str(tKC['sell']).ljust(10)+" (spread: "+str(spread)+"%)"
	print(ps)
	if('sendBalance' in actions):
		telegramBot.text_message(balanceStr + "\n" + ps)


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
		if(maxNow > conf('general.min_trade_size','float')) and conf('general.trading_enabled','bool'):
			maxLeftTotal = getTradeLeftTotal(symbol)
			print("Most I can trade now is: "+str(maxNow)+" "+symbol+" of "+str(maxLeftTotal)+" total.")
			if(conf('KuCoin.disable_buy','bool')):
				print("Not allowed to buy from KuCoin. Skipping trade.")
				exit()
			if(conf('BitGrail.disable_sell','bool')):
				print("Not allowed to sell to BitGrail. Skipping trade.")
				exit()
			# Update limits (whatever happens next)
			updateLimits(symbol,maxNow)
			# Get buy price on market A (KC)
			buyAt = tKC['sell']*1.01 # asking price to get it at instantly

			# TODO: check order book if enough is actually available at that price!
			# Get selling price on market B (BG)
			sellAt = tBG['buy']*0.99 # price people already want to buy it at
			# Place order on market A (KC)
			if(buyAt > sellAt):
				s = "I'm paying more on BitGrail than I'm getting from the sale on KuCoin (buyAt: "+str(buyAt)+", sellAt: "+str(sellAt)+")!"
				print(s)
				telegramBot.text_message(s)
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
			if(conf('general.trading_enabled','bool')):
				print("Not allowed to trade this small amount!")
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
		if(maxNow > conf('general.min_trade_size','float')) and conf('general.trading_enabled','bool'):
			maxLeftTotal = getTradeLeftTotal(symbol)
			print("Most I can trade now is: "+str(maxNow)+" "+symbol+" of "+str(maxLeftTotal)+" total.")
			if(conf('BitGrail.disable_buy','bool')):
				print("Not allowed to buy from BitGrail. Skipping trade.")
				exit()
			if(conf('KuCoin.disable_sell','bool')):
				print("Not allowed to sell to KuCoin. Skipping trade.")
				exit()
			# Update limits (whatever happens next)
			updateLimits(symbol,maxNow)
			# Get buy price on market A (BG)
			buyAt = tBG['sell']*1.01 # asking price to get it at instantly
			# TODO: check order book if enough is actually available at that price!
			# Get selling price on market B (KC)
			sellAt = tKC['buy']*0.99 # price people already want to buy it at
			# Place buy order on market A (BG)
			if(tBG['sell'] > tKC['buy']):
				s = "would potentially have paid more to buy that I'd get to sell. Not doing anything!"
				print(s)
				telegramBot.text_message(s)
			else:
				traded = True
				traded_amount = -maxNow
				s = "BitGrail: creating buy order of "+str(maxNow)+" "+symbol+" at "+str(buyAt)+"."
				print(s)
				bg_balance = bgm.getBalance()
				if(bg_balance[symbol_base] < maxNow * buyAt):
					s = s + "Not enough coins.\n"
					print "Crap. I ran out of "+symbol_base+" on the exchange... Want to buy: "+str(maxNow)+" for "+str(maxNow * buyAt)+" BTC but I have a balance of "+str(bg_balance[symbol_base])+" "+symbol_base+" on BitGrail."
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
			if(conf('general.trading_enabled','bool')):
				print("Not allowed to trade this small amount!")
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
	if(margin <= 2.0):
		# FIXME: Doesn't work for currencies that are more expensive than XRB
		# For ETH margin*4 basically means, any bit of margin and it sells the limit
		# maxNow = min(0+round(margin*4),maxNow)
		# Trying this instead:
		maxNow = min(round(2*margin/2.0*maxNow),maxNow)
		print("Capped order to "+str(maxNow)+" (profit margin only "+str(round(margin,2))+"% above minimum)")
	# Cap quantity to available balance
	if(maxNow > availableForSale):
		print('Not selling more that available. You have: '+str(availableForSale)+' '+symbol+'. So capping to that.')
		maxNow = min(maxNow,availableForSale)
	return maxNow

def getTradeMaxNow(symbol):
	TradeLimits = ConfigParser.ConfigParser()
	TradeLimits.read('./trade_allowed.ini')
	max_qty_left = float(TradeLimits.get(symbol,'max_qty_left'))
	s = "I'm allowed to trade (max_qty_left > 0.0)."
	if(max_qty_left == 0.0):
		s = "Trade limit reached. Use /limit_left 1000 to increase again."
	telegramBot.text_message(s,topic="Limit."+symbol+".trade_allowed.reached")
	return min(max_qty_left,float(TradeLimits.get(symbol,'max_per_trade')))

def getTradeLeftTotal(symbol):
	TradeLimits = ConfigParser.ConfigParser()
	TradeLimits.read('./trade_allowed.ini')
	if(TradeLimits.get(symbol,'self_abort') != 'False'):
		quit("Aborting trading. Reason: " + TradeLimits.get(symbol,'self_abort'))
	return float(TradeLimits.get(symbol,'max_qty_left'))



if __name__ == "__main__":
    main()


