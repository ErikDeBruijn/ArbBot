# -*- coding: utf-8 -*-

import bitgrail
import ConfigParser
import pprint
import requests 
from time import sleep, time
from requests_toolbelt.utils import dump
import re
import pickle
import sys

# Run me with "python -i bitgrail_mimic.py" to run arbitrary functions interactively
# FIXME: allow it to work when no working serialized session exists.

class Bitgrail_mimic():

    def __init__(self):
        self._session_ = None
        self._selfTestedOK = False
        self._balance_cached = None
        self._symbol = None
        self._symbol_base = None

    def set_coin(self,symbol,symbol_base):
        self._symbol = symbol
        self._symbol_base = symbol_base
        self._market = symbol_base + '-' + symbol

    def store_session(self):
        return pickle.dumps(self._session_)

    def load_session(self):
        # deserialize session
        try:
            with open('bg_session.dump') as fh:
                sdump = fh.read()
                self._session_ = pickle.loads(sdump)
        except:
            print "Could not read or load an existing session."
            self.newSession()

    def ensure_working_session(self):
        if(self._selfTestedOK): return True
        if(not self._session_): self.load_session()
        balance = self.getBalance(selfTest=True)
        if(not balance):
            print "Session needs to be recreated..."
            session = self.newSession()
        else:
            print "Tested existing session. Reusing that..."

        balance = self.getBalance(selfTest=True)
        if(balance):
            self._selfTestedOK = True
            return True
        else:
            print("Could not ensure a working session.")
            quit("You may have to run me interactively and specify the 2FA token on input.")

    def parseBalance(self,htmlbody,coin):
        re_result = re.search(coin.upper().strip()+' - Balance.*>([0-9].*)<',htmlbody)
        if(re_result):
            return float(re_result.group(1))
        else:
            return False

    def createOrder(self,market,buySell,amount,price):
        self.ensure_working_session()
        if(buySell.upper() == 'SELL'):
            orderType = '0'
        elif(buySell.upper() == 'BUY'):
            orderType = '1'
        else:
            quit("Create order can only be called with \'buy\' or \'sell\'.")
        newOrder = '1'
        price = '{:.8f}'.format(round(float(price),8))
        fee = '{:.8f}'.format(round(0.002 * float(amount) * float(price),8))
        buyTotal = '{:.8f}'.format(round(float(fee)+float(amount)*float(price),8))
        payload = {
            'amount':(None, str(amount)), 
            'price':(None, str(price)), 
            'fee':(None, str(fee)),
            'buyTotal':(None, str(buyTotal)), 
            'newOrder':(None, newOrder), 
            'orderType':(None, orderType), 
            'ajax':(None, '1')
        }
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'referrer': 'https://bitgrail.com/market/'+market,
            'x-requested-with': 'XMLHttpRequest'
        } 
        # Next time the balance is checked, assume it needs updating from server
        self._balance_cached = None
        resp = self._session_.post('https://bitgrail.com/market/'+market,headers=headers, files=payload)
        print("DEBUG: bitgrail_mimic got: " + resp.text.encode("utf-8"))
        if(not resp.text.find('icon-ok-circled')):
            return None
        else:
            #FIXME: return order ID
            return True

    def getBalance(self,selfTest=False):
        if(not selfTest): self.ensure_working_session()
        # FIXME: some balance can be reserved, better to use /wallets for info!
        if(selfTest):
            t_symbol = self._symbol
            t_symbol_base = self._symbol_base
            t_market = self._market
            self._symbol = 'XRB'
            self._symbol_base = 'BTC'
            self._market = 'BTC-XRB'
        if(not self._balance_cached):
            resp = self._session_.get("https://bitgrail.com/market/"+self._market)
            self._balance_cached = resp.text
        balance = {}
        balance[self._symbol_base] = self.parseBalance(self._balance_cached,self._symbol_base)
        balance[self._symbol] = self.parseBalance(self._balance_cached,self._symbol)
        if(selfTest):
            self._symbol = t_symbol
            self._symbol_base = t_symbol_base
            self._market = t_market
        if(balance[self._symbol_base]):
            return balance
        return False

    def newSession(self):
        start_time = time()

        print "Starting a new BitGrail session with Captcha."
        Config = ConfigParser.ConfigParser()
        Config.read("./.settings.ini")

        email = Config.get("BitGrail",'email')
        password = Config.get("BitGrail",'password')

        API_KEY_2CAPTCHA = Config.get("2captcha",'2CAPCHA_API_KEY')
        recapcha_sitekey = Config.get("BitGrail",'recapcha_sitekey') # bitgrail

        submit_url = "https://bitgrail.com/login"

        # http://scraping.pro/2captcha-service-to-solve-recaptcha-2/
        # send credentials to the service to solve captcha
        # returns service's captcha_id of captcha to be solved
        url="http://2captcha.com/in.php?key="+API_KEY_2CAPTCHA+"&method=userrecaptcha&googlekey="+recapcha_sitekey+"&pageurl="+submit_url
        resp = requests.get(url) 
        if resp.text[0:2] != 'OK':
            print(resp.text)
            quit('Error. Captcha is not received')
        captcha_id = resp.text[3:]
        # print("Captcha ID = ",captcha_id)
        if(captcha_id[0:3] == 'OR_'):
            quit("Error: " + captcha_id)

        # fetch ready 'g-recaptcha-response' token for captcha_id  
        fetch_url = "http://2captcha.com/res.php?key="+API_KEY_2CAPTCHA+"&action=get&id=" + captcha_id

        print "Waiting for captcha to be solved by mechanical Turk..."
        captcha_ok = False
        for i in range(1, 200):	
            sleep(1)
            resp = requests.get(fetch_url)
            print ".",
            sys.stdout.flush()
            if resp.text[0:2] == 'OK':
                captcha_ok = True
                break
        if(captcha_ok != True):
            quit("Captcha isn't OK after "+(time() - start_time)+" s: "+resp.text)
        		
        print('\nDone. Time to solve captcha: ', time() - start_time) 

        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'referrer': 'https://bitgrail.com/login',
            'x-requested-with': 'XMLHttpRequest'
        } 
            # POST parameters, might be more, depending on form content

        # resp = requests.post(submit_url, headers=headers, files=payload)
        self._session_ = requests.Session()
        self._session_.get("https://bitgrail.com/")

        payload = {'email':(None, email), 'ajax':(None, '1'), 'password':(None, password), 'login':(None, '1'), 'submit':(None,  'Login'), 'g-recaptcha-response':(None,  resp.text[3:])  }
        resp = self._session_.post(submit_url, headers=headers, files=payload)
        # print(resp.text)

        if(not resp.text.find('icon-ok-circled')):
            print "BitGrail: printing full dump or response"
            # data = dump.dump_response(resp)
            # print(data.decode('utf-8'))
            print resp.text
            quit("No valid response from login.")

        submit_url = "https://bitgrail.com/login2fa"
        two_factor_token = raw_input("Enter your 2FA code: ").strip()
        print("You entered: "+two_factor_token)

        payload = {'token2fa': (None,two_factor_token),'login2fa': (None,'1'), 'ajax': (None,'1')}
        resp = self._session_.post(submit_url, headers=headers, files=payload)
        # print(resp.text)

        if(not resp.text.find('icon-ok-circled')):
            print "BitGrail: printing full dump or response"
            # data = dump.dump_response(resp)
            # print(data.decode('utf-8'))
            print resp.text
            quit("No valid response from login.")

        sdata = self.store_session()
        with open("bg_session.dump","w") as f:
            f.write(sdata)
        return self._session_

    def checkPageForString(self,url,s):
        resp = self._session_.get(url)
        if(resp.text.find(s) >= 0):
            return True
        return False

    def checkWithdrawals(self,coin):
        self.ensure_working_session()
        s = 'withdraw under maintenance'
        result = self.checkPageForString('https://bitgrail.com/withdraw/'+coin.upper(),s)
        return not result

# end of functions

def main():
    bgm = Bitgrail_mimic()
    bgm.set_coin('XRB','BTC')

    if(bgm.checkWithdrawals('xrb')):
        print "Withdrawals are open."
    else:
        print "Withdrawals under maintenance."

    balance = bgm.getBalance('BTC-XRB')
    print "Balances:",balance

    # bgm.createOrder('BTC-XRB','buy',amount=0.1,price=0.001)

if __name__ == "__main__":
    main()





# result = bg.post('sellorder',market='BTC-XRB',amount=str(maxNow),price=str(price))
# withdraw_amount = 5
# address = "xrb_31rxfkkxpyemf6agz9ojy9rcxwpuqgxb5ir1yy3zetf49wcmhw47pbsksk9h" # desktop wallet

# result = bg.post('withdraw',market='XRB',amount=str(withdraw_amount),address=address)

# 6Lfs1BkUAAAAAIMOAKtQqnaF95YpuY_siUPEaa7V
#<textarea id="g-recaptcha-response" name="g-recaptcha-response" class="g-recaptcha-response"
# style="width: 250px; height: 40px; border: 1px solid #c1c1c1; margin: 10px 25px; padding: 0px; 
#resize: none;  display: none; "></textarea>

# Buy order, POST /market/BTC-XRB

# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# 
# Content-Disposition: form-data; name="amount"

# 1
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# Content-Disposition: form-data; name="price"

# 0.0017471182
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# Content-Disposition: form-data; name="fee"

# 0.00000349
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# Content-Disposition: form-data; name="buyTotal"

# 0.00175061
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# Content-Disposition: form-data; name="newOrder"

# 1
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# Content-Disposition: form-data; name="orderType"

# 1
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv
# Content-Disposition: form-data; name="ajax"

# 1
# ------WebKitFormBoundarySVM4GOnyWUBRaIkv--

