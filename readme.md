Approach
========

Markets A and B have a price difference for a currency pair. E.g. B has a discount, even when taking into account bid-ask spreads.

Goal
====

Primary goal: 
 - When arb opportunity arises, buying cheap on the B side and sell high on the A side.

Secondary goal:
 - Capital management (Ensure funds are there to trade by transfering between exchanges or allow time-based rebalancing)
 - When lots of selling happened on one exchange it buids up BTC, it increments a counter.
 - Another that buys a lot will get a shortage of BTC. It decrements a counter.
 - When an exchange is below the threshold and there is enough supply on another, suggest the transfer of BTC. The threshold needs to be high enough to minimize withdrawal fees.

Development
===========

Steps:
 1. Get APIs and code to get order book data for one exchange.
 2. Get it for the second exchange.
 3. Analyse when an arb opportunity arises and suggest what to do manually.
 4. Instead of analyzing once, make it continue to scrape until ArbOpp arises.
 5. Allow the trade to actually happen.

Notes
=====

Exchanges used:
 - Kucoin (combined with https://github.com/sammchardy/python-kucoin )
 - BitGrail (combined with https://github.com/rwoods02/bitgrail/blob/develop/bitgrail.py )
