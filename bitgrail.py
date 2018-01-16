#!/usr/bin/env python

import json
import requests
# temporarily?
from requests_toolbelt.utils import dump
# requires: pip install requests_toolbelt

import pprint
import os
import hmac
import hashlib
from itertools import count
import time
import sys
from lxml import html
from lxml import etree
import numpy as np


# store as a global variable
NONCE_COUNTER = count(int(time.time() * 1000))


class Bitgrail():

    def __init__(self,aKey = '',aSecret = ''):
        self._url_ = "https://bitgrail.com/api/v1/"
        self._payload_ = {'nonce': ''}
        self._key = aKey
        self._secret = aSecret
        self._get_set_ = set(['markets', 'ticker', 'orderbook', 'tradehistory'])
        self._post_set_ = set(['balances', 'buyorder', 'sellorder', 'openorders', 'cancelorder'
                               'getdepositaddress','withdraw', 'lasttrades', 'depositshistory', 'withdrawshistory'])

    # def setAuth(self,aKey,aSecret):
    #     self._key = aKey
    #     self._secret = aSecret
    def getOrderBook(self,pair=None):
    	url = "https://bitgrail.com/market/"+pair
    	r = requests.get(url)
    	tree = html.fromstring(r.text)
    	asks = tree.xpath('//*[@id="sellOpened"]/tbody/tr[position() < 15]/td/text()')
    	asks = np.reshape(asks, (len(asks)/5,5))
    	bids = tree.xpath('//*[@id="buyOpened"]/tbody/tr[position() < 15]/td/text()')
    	bids = np.reshape(bids, (len(bids)/5,5))
    	return (asks,bids)


    def get(self, endpoint, pair=None):
        # check if proper endpoint
        if endpoint not in self._get_set_:
            print "Most likely you are hitting the incorrect endpoint. Please verify you are using an endpoint from list below"
            print(self._get_set_)
            sys.exit()

        # Create endpoint for pairs
        if pair:
            endpoint = pair + "/" + endpoint

        # perform get request and parse output
        r = requests.get(self._url_ + endpoint)
        json_data = json.loads(r.text)

        # Check for successful message
        if not json_data["success"]:
            print "unsuccessful request, exchange could be down"
            sys.exit()

        response = json_data['response']

        # print for debugging purposes
        # pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(response)
        return response

    def post(self, endpoint, coin=None, amount=None, price=None, address=None, uuid=None, market=None):
        # check if proper endpoint
        if endpoint not in self._post_set_:
            print "Most likely you are hitting the incorrect endpoint. Please verify you are using an endpoint from list below"
            print(self._get_set_)
            sys.exit()

        headers = {'KEY': self._key,
                   'SIGNATURE': ''}

        # # iterate the nonce
        self._payload_['nonce'] = (None, next(NONCE_COUNTER))

        # payload to send
        self._payload_['coin'] = (None,coin)
        self._payload_['market'] = (None, market)
        self._payload_['amount'] = (None, str(int(float(amount))))
        # <added by="Erik">
        self._payload_['price'] = (None, price)
        # </added>
        self._payload_['address'] = (None, address)
        self._payload_['id'] = (None, uuid)

        # Prepare request object
        request = requests.Request(
            'POST', self._url_ + endpoint, headers=headers, files=self._payload_)
        prepped = request.prepare()

        # encrypted POST parameters with HMAC-SHA512 alghoritm using your secret API key
        signature = hmac.new(self._secret, prepped.body, digestmod=hashlib.sha512)
        prepped.headers['SIGNATURE'] = signature.hexdigest()

        r = None

        # The end of the with block closes the session
        with requests.Session() as session:
            r = session.send(prepped)
            print "BitGrail: printing full dump or response"
            data = dump.dump_response(r)
            print(data.decode('utf-8'))
            print "BitGrail: printing errorcode"
            print(r)
            # print "BitGrail: Printing object (if any)"
            # print(r.text)

        return r

