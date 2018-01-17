
# For coin names we want to use the name that when lowercased, it yields a correct
# coinmarketcap.com/currencies/{name}/ link
coinInfo = {
	'BTC': { 'name': 'Bitcoin' },
	'XRB': { 'name': 'Raiblocks' },
	'ETH': { 'name': 'Ethereum' },
	'XRP': { 'name': 'Ripple' },
}

def getCoinInfoFromSymbol(symbol):
	symbol = symbol.upper()
	if(symbol in coinInfo):
		return coinInfo[symbol]

def getCoinNameFromSymbol(symbol):
	ci = getCoinInfoFromSymbol(symbol)
	if('name' in ci):
		return ci['name']
	return None

def getCoinLink(symbol):
	ci = getCoinInfoFromSymbol(symbol)
	if('link' in ci):
		return coinInfo[symbol]['link']
	return 'https://coinmarketcap.com/currencies/'+coinInfo[symbol]['name'].lower()+'/'

