# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html

import plotly.graph_objs as go
import plotly.plotly as py
import plotly.figure_factory as ff

import socket
import datetime, time


def to_unix_time(dt):
    epoch =  datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000

import pandas as pd

#                          time  bitgrail_sell  bitgrail_buy  kcoin_sell  \
# 0  2018-01-06T01:58:30.214749       0.001944      0.001926    0.001989
# 1  2018-01-06T01:58:42.176539       0.001950      0.001926    0.001989
# 2  2018-01-06T01:58:54.274793       0.001948      0.001926    0.001989
# 3  2018-01-06T01:59:06.321532       0.001950      0.001927    0.001989
# 4  2018-01-06T01:59:18.308838       0.001950      0.001930    0.001989

#    kcoin_buy profitKC2BG profitBG2KC  traded
# 0    0.00198      -3.46%       1.55%     NaN
# 1    0.00198      -3.46%       1.24%     NaN
# 2    0.00198      -3.46%       1.34%     NaN
# 3    0.00198      -3.41%       1.24%     NaN
# 4    0.00198      -3.26%       1.24%     NaN
def getLayout():
    print "===== gathering latest data ====="
    skipfirst = 1500
    skiprows = range(1,skipfirst+1)
    cols = ['time','bitgrail_sell','bitgrail_buy','kcoin_sell','kcoin_buy','traded']
    df = pd.read_csv("log.csv",delimiter='\t',usecols=cols,header=0,parse_dates=[0],skiprows=skiprows)
    # dfBG = pd.read_csv("log.csv",delimiter='\t',usecols=['time','bitgrail_sell'],header=0,parse_dates=[0],skiprows=skiprows)
    # dfKC = pd.read_csv("log.csv",delimiter='\t',usecols=['time',],header=0,parse_dates=[0],skiprows=skiprows)

    # df = pd.read_csv(
    #     'https://gist.githubusercontent.com/chriddyp/' +
    #     '5d1ea79569ed194d432e56108a04d188/raw/' +
    #     'a9f9e8076b837d541398e999dcbac2b2826a81f8/'+
    #     'gdp-life-exp-2007.csv')

    print(df.head())

    # exit()
    # table = ff.create_table(df)

    trace = {}
    trace['BG_sell'] = go.Scatter(
        x = df['time'],
        y = df['bitgrail_sell'],
        yaxis = 'y',
        name = 'bitgrail_sell',
        line = dict(
            color = ('rgb(6, 102, 12)'),
            width = 1)
    )
    trace['BG_buy'] = go.Scatter(
        x = df['time'],
        y = df['bitgrail_buy'],
        yaxis = 'y',
        name = 'bitgrail_buy',
        line = dict(
            color = ('rgb(12, 205, 24)'),
            width = 1)
    )
    trace['KC_sell'] = go.Scatter(
        x = df['time'],
        y = df['kcoin_sell'],
        yaxis = 'y',
        name = 'kcoin_sell',
        line = dict(
            color = ('rgb(22, 96, 167)'),
            width = 1)
    )
    trace['KC_buy'] = go.Scatter(
        x = df['time'],
        y = df['kcoin_buy'],
        yaxis = 'y',
        name = 'kcoin_buy',
        line = dict(
            color = ('rgb(31, 134, 233)'),
            width = 1)
    )
    trace['traded'] = go.Bar(
        x = df['time'],
        y = df['traded'],
        yaxis = 'y2',
        name = 'traded',
        # color = ('rgb(255, 145, 0)'),
        width = 0.4
    )

    data = [trace['BG_sell'], trace['BG_buy'], trace['KC_sell'], trace['KC_buy']]
    # data = [trace['BG_sell'], trace['BG_buy'], trace['KC_sell'], trace['KC_buy'], trace['traded']]

    # Edit the layout
    layout = dict(title = 'Prices of exchanges',
                  xaxis = dict(
                    title = 'Time',
                    range = [1000*time.time()-60*60*24000,1000*time.time()],
                    rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                             label='1h',
                             step='hour',
                             stepmode='backward'),
                        dict(count=6,
                             label='6h',
                             step='hour',
                             stepmode='backward'),
                        dict(count=24,
                             label='24h',
                             step='hour',
                             stepmode='backward'),
                        dict(count=3,
                             label='3d',
                             step='day',
                             stepmode='backward'),
                                dict(step='all')
                                ])
                    ),
                    
                    type='date'),
                  yaxis = dict(title = 'Price (BTC)'),
                  yaxis2 = dict(title = 'Revenue (BTC)', side='right',overlaying='y')
                  
                  )

    layout['annotations'] = [
        dict(xref='paper', yref='paper', x=0.95, y=.5,
              xanchor='center', yanchor='top',
              text='Diff: ',
              font=dict(family='Arial',
                        size=10,
                        color='rgb(150,150,150)'),
              showarrow=False)
    ]

    config = {'scrollZoom': True}
    fig = dict(data=data, layout=layout)
    graphObject = dcc.Graph(
        id='prices',
        figure=fig,config=config
    )
    layout = html.Div(children=[
    html.Div(children='Last data fetch: ' + str(datetime.datetime.now())),

    graphObject
    ])
    return layout


app = dash.Dash()

# fig = createFig()


app.layout = getLayout

PORT = 8050
ADDRESS = '0.0.0.0'

if __name__ == '__main__':
    app.run_server(port=PORT, host=ADDRESS, debug=True)
