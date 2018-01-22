

import ConfigParser
from ConfigParser import SafeConfigParser
import socket

import pprint
import csv
import datetime
import CoinData
from Telegram import Telegram
# from modules.Telegram import Telegram
def setConfig(heading,k,val):
	parser = SafeConfigParser()
	parser.read('./trade_allowed.ini')
	parser.set(heading,k,str(val))
	with open('./trade_allowed.ini', 'wb') as configfile:
		parser.write(configfile)

def getConfig(heading,k):
	parser = SafeConfigParser()
	parser.read('./trade_allowed.ini')
	return parser.get(heading,k)


def conf(topicDotKey,type='string'):
	(topic,k) = topicDotKey.split('.')
	if(type in ('boolean','bool')):
		return Config.get(topic,k).lower() in ("yes", "true", "t", "1")
	if(type in ('float')):
		return float(Config.get(topic,k))
	return Config.get(topic,k)


def getIp():
    return str([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), 
s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, 
socket.SOCK_DGRAM)]][0][1]]) if l][0][0])


def logCSV(vars):
	with open(conf('general.logFilePrefix')+'_'+symbol+'-'+symbol_base+'.csv','a') as f:
		writer = csv.writer(f, delimiter='\t')
		writer.writerow(vars)

Config = ConfigParser.ConfigParser()
Config.read("./.settings.ini")

dt = datetime.datetime.now().isoformat()

pp = pprint.PrettyPrinter(indent=4)

symbol = conf('general.symbol').upper()
symbol_base = conf('general.symbol_base').upper()
symbol_name = CoinData.getCoinNameFromSymbol(symbol)

graphURL = "http://"+ getIp() + ":"+conf('webserver.webServerPort')+"/"

telegramBot = Telegram(conf('Telegram.telegram_bot_id'))
telegramBot.set_chat_id(conf('Telegram.telegram_chat_id'))

min_perc_profit = {'KC': conf('KuCoin.buy_at_min_perc_profit','float'), 'BG': conf('BitGrail.buy_at_min_perc_profit','float')}
