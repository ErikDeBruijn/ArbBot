#!/usr/bin/env python


class ArbAnalysis():

    def __init__(self):
        self._orderbook_ = None
        self._asks = []
        self._bids = []

    # ASK: lowest price anyone's willing to sell at is the ASK.
    # BID: highest price anyone's willing to buy at is the BID.

    # Best price to get it right now: ASK.
    # Best price to set all is the BID.

    # Ask (sell) > Bid (buy)

    # def setAuth(self,aKey,aSecret):
    #     self._key = aKey
    #     self._secret = aSecret
    def parse_book(self, orderbook, side):
        asks = len(orderbook[side])
        max_count = 20
        print(str(asks) + " "+ side +".")
        for i in range(asks-1,0,-1):
            order = orderbook[side][i]
            print(side+": price = "+str(order['price'])+", amount = "+str(order['amount']))
            if side == 'ask':
                self._asks.append(order)
            elif side == 'bid':
                self._bid.append(order)
            max_count = max_count - 1
            if(max_count < 0):
                break

    def parse_orders(self, orderbook):
        self.parse_book(orderbook,'asks')
        self.parse_book(orderbook,'bids')
