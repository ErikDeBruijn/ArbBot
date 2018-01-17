# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

import plotly
import plotly.graph_objs as go
import plotly.plotly as py
import plotly.figure_factory as ff

from modules.CoinData import CoinData

import datetime, time

import pandas as pd

import flask
import glob
import os

import ConfigParser

Config = ConfigParser.ConfigParser()
Config.read("./.settings.ini")

def conf(topicDotKey,type='string'):
    (topic,k) = topicDotKey.split('.')
    if(type in ('boolean','bool')):
        return Config.get(topic,k).lower() in ("yes", "true", "t", "1")
    if(type in ('float')):
        return float(Config.get(topic,k))
    return Config.get(topic,k)

app = dash.Dash()

symbol = Config.get("general",'symbol').upper()
symbol_name = getCoinNameFromSymbol(symbol)
symbol_base = Config.get("general",'symbol_base').upper()

logFilePrefix = Config.get("general",'logFilePrefix')

logFile = logFilePrefix+'_'+symbol+'-'+symbol_base+'.csv'

image_directory = '/Users/erik/Dev/cryptocurrency/arbbot/assets/128x128/'
list_of_images = [os.path.basename(x) for x in glob.glob('{}*.png'.format(image_directory))]
static_image_route = '/static/'
# print list_of_images

def to_unix_time(dt):
    epoch =  datetime.datetime.utcfromtimestamp(0)
    return (dt - epoch).total_seconds() * 1000


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

app.title = symbol+'-'+symbol_base+' [' + conf('general.instance_name') +']'

intervalObject = dcc.Interval(id='interval-component', interval=20*1000)
checkList = dcc.Checklist(
    id = 'checklist',
    options=[
        {'label': 'Display Trades', 'value': 'trades'},
        {'label': 'Remember View', 'value': 'lockView'}
    ],
    values=['trades','lockView'],
    labelStyle={'display': 'inline-block'}
)

app.layout = html.Div(children=[
    html.Div(children=[
        intervalObject,
        html.Link(rel="shortcut icon", href="favicon.ico"), #, type="image/x-icon"
        html.Img(src='/static/'+symbol_name.lower()+'.png'),
        checkList,
        html.Div(id='lastUpdate')]),    
        dcc.Graph(id='prices-graph',config={'scrollZoom': True})
])


@app.callback(Output('lastUpdate', 'children'),[Input('interval-component', 'n_intervals')])
def lastUpdate(n):
    return 'Last updated: ' + str(datetime.datetime.now())

@app.callback(
    Output(
        'prices-graph', 'figure'),
        [Input('interval-component', 'n_intervals'),Input('checklist','values')],
        [State('prices-graph', 'relayoutData')]
)
def getGraph(n,checkBoxes,relayout_data):
    print "checkboxes: "+str(checkBoxes)
    # relayout_data contains data on the zoom and range actions
    print("relayout_data: "+str(relayout_data))
    # FIXME: it only remembers the specific axis that was most recently changed
    print "===== gathering latest data =====" + symbol + '-' + symbol_base
    skipfirst = int(Config.get("webserver",'skipFirstNum'))
    skiprows = range(1,skipfirst+1)
    cols = ['time','bitgrail_sell','bitgrail_buy','kcoin_sell','kcoin_buy','traded']
    # print(df.head())
    df = pd.read_csv(logFile,delimiter='\t',usecols=cols,header=0,parse_dates=[0],skiprows=skiprows)

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

    # Edit the layout
    layout = dict(title = 'Prices for ' + symbol + '-' + symbol_base + ' on two exchanges [' +Config.get("general",'instance_name')+']',
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
                  height = 700
                  )
    if('trades' in checkBoxes):
        df_filtered = df.query('traded>=0')
        trace['bought'] = go.Bar(
            x = df_filtered['time'],
            y = df_filtered['traded'],
            yaxis = 'y2',
            name = 'bought on BitGrail',
            # color = ('rgb(255, 145, 0)'),
            marker=dict(
                color='rgb(158,202,225)',
                line=dict(
                    color='rgb(31, 134, 233',
                    width=2,
                )
            ),
            opacity=0.4,
        )

        df_filtered = df.query('traded<0')
        trace['sold'] = go.Bar(
            x = df_filtered['time'],
            y = df_filtered['traded']*-1,
            yaxis = 'y2',
            name = 'bought on KuCoin',
            marker=dict(
                color='rgb(158,202,225)',
                line=dict(
                    color='rgb(12, 205, 24)',
                    width=2,
                )
            ),
            opacity=0.4,
        )
        layout['yaxis2'] = {'title': '# of '+symbol_name+' bought & sold ('+symbol+')', 'side':'right', 'overlaying':'y'}
        data = [trace['BG_sell'], trace['BG_buy'], trace['KC_sell'], trace['KC_buy'],trace['bought'],trace['sold']]
    else:
        data = [trace['BG_sell'], trace['BG_buy'], trace['KC_sell'], trace['KC_buy']]

    if relayout_data and ('lockView' in checkBoxes):
        if 'xaxis.range[0]' in relayout_data:
            layout['xaxis']['range'] = [
                relayout_data['xaxis.range[0]'],
                relayout_data['xaxis.range[1]']
            ]
        if 'yaxis.range[0]' in relayout_data:
            layout['yaxis']['range'] = [
                relayout_data['yaxis.range[0]'],
                relayout_data['yaxis.range[1]']
            ]
        if 'yaxis2.range[0]' in relayout_data and 'yaxis2' in layout:
            layout['yaxis2']['range'] = [
                relayout_data['yaxis2.range[0]'],
                relayout_data['yaxis2.range[1]']
            ]

    layout['annotations'] = [
        dict(xref='paper', yref='paper', x=0.95, y=.5,
              xanchor='center', yanchor='top',
              text='Diff: ',
              font=dict(family='Arial',
                        size=10,
                        color='rgb(150,150,150)'),
              showarrow=False)
    ]

    return {'data': data, 'layout': layout}



PORT = int(Config.get("webserver",'webServerPort'))
ADDRESS = '0.0.0.0'

@app.server.route('/favicon.ico')
def favicon():
    print "flask.send_from_directory(image_directory="+image_directory+", image_name="+symbol_name.lower()+'.png'+")"
    return flask.send_from_directory(image_directory,symbol_name.lower()+'.png')

@app.server.route('{}<image_path>.png'.format(static_image_route))
def serve_image(image_path):
    image_name = '{}.png'.format(image_path)
    if image_name not in list_of_images:
        raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
    print "flask.send_from_directory(image_directory="+image_directory+", image_name="+image_name+")"
    return flask.send_from_directory(image_directory, image_name)


if __name__ == '__main__':
    app.run_server(port=PORT, host=ADDRESS, debug=True)
