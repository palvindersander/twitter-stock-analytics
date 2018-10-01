from datetime import datetime, timedelta
import tweepy
import threading
import json
import time
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Event, Input, Output, State

from analysis import createFigure, getKeys, getStockDayData, getDataMeta, getCumulativeData, getTweetsPerSecondData

#open('data.txt', 'w').close()

def streamData(terms):

    tweets = []

    global api
    global miningThread

    def saveTweets():
        with open('data.txt', 'w') as outfile:
            print('saving tweets')
            json.dump(tweets, outfile)
        outfile.close()

    class twitterStream(tweepy.StreamListener):
        def __init__(self):
            super().__init__()
            self.startTime = datetime.now() + timedelta(seconds=2)

        def on_status(self, status):
            tweets.append(json.dumps(status._json))
            if datetime.now() >= self.startTime:
                self.startTime = self.startTime + timedelta(seconds=2)
                saveTweets()

        def on_error(self, status_code):
            if status_code == 420:
                return True
            return True

        def on_timeout(self):
            return True

    twitterStream = twitterStream()
    stream = tweepy.Stream(auth=api.auth, listener=twitterStream)
    stream.filter(track=[terms], async=True)

    while True:
        if not miningThread:
            stream.disconnect()
            del stream
            saveTweets()
            return
        time.sleep(0.5)

keys = getKeys()
miningThread = True

#with open('data.txt', 'w') as outfile:
    #json.dump([], outfile)
#outfile.close()

auth = tweepy.OAuthHandler(keys['twitterCKey'], keys['twitterCSecret'])
auth.set_access_token(keys['twitterAToken'], keys['twitterASecret'])
api = tweepy.API(auth)

app = dash.Dash(__name__)
server = app.server
app.css.append_css(
    {'external_url': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css'})

app.layout = html.Div(style={'backgroundColor': '#FFF', 'margin': '50px'}, className='', children=[

    html.Div([

        html.Div([

            html.H1([
                'Twitter Analytics',
                html.Span(
                    children='LIVE',
                    className='badge badge-secondary',
                    style={'marginLeft': '15px'}
                )
            ], className='display-4'),
            html.P(
                children='Built by Palvinder Sander using Python (Dash Framework)', className='lead'),

        ], className='container', style={'margin': '-15px', 'padding': '0px'}),

    ], className='jumbotron jumbotron-fluid', style={'backgroundColor': '#FFF'}),

    html.Div([

        html.H4(children='Sorry to interrupt - Instructions', className='alert-heading'),

        html.P(children='With the Dash framework being fragile of sorts, there are some bugs, that I am working on, that you must work around in order to use this tool.'),

        html.Hr(),

        html.P(children='submit a term > click "show" after 5 seconds > submit a ticker'),
        html.P(children='After this the app will work like I intended :)'),

    ], className='alert alert-danger', style={'marginBottom' : '100px'}),

    html.Div([

        html.Div([

            dcc.Input(
                id='termInput',
                placeholder='stream term',
                className='col-6',
                type='text',
            ),

            html.Button(
                id='termSubmit',
                children='submit term',
                className='btn btn-primary col offset-md-1',
                n_clicks=0
            ),

            html.Button(
                id='showCumulation',
                children='show',
                className='btn btn-primary col offset-md-1',
                n_clicks=0
            ),

        ], className='row'),

        dcc.Graph(
            id='twitterGraph'
        ),

        dcc.Interval(
            id='updateTwitterGraph',
            interval=4 * 1000,
            n_intervals=0
        ),

    ]),

    html.Div([

        html.Div([

            dcc.Input(
                id='tickerInput',
                placeholder='stock ticker',
                className='col-4',
                type='text'
            ),

            html.Div([
                dcc.Dropdown(
                    id='stockTimeRange',
                    placeholder='stock time range',
                    options=[
                        {'label': '1 DAY', 'value': '1d'},
                        {'label': '1 MONTH', 'value': '1m'},
                        {'label': '3 MONTHS', 'value': '3m'},
                        {'label': '6 MONTHS', 'value': '6m'},
                        {'label': 'YEAR TO DATE', 'value': 'ytd'},
                        {'label': '1 YEAR', 'value': '1y'},
                        {'label': '2 YEARS', 'value': '2y'},
                        {'label': '5 YEARS', 'value': '5y'}]
                ),
            ], className='col-5'),

            html.Button(
                id='tickerSubmit',
                children='submit ticker',
                className='btn btn-primary col offset-md-1',
                n_clicks=0
            ),

        ], className='row'),

        dcc.Graph(
            id='stockPriceGraph',
            animate=True,
        ),

        dcc.Interval(
            id='updateStockGraph',
            interval=60 * 1000,
            n_intervals=0
        )

    ],
    ),

    html.P(id='streamBuffer'),

]
)

@app.callback(Output('twitterGraph', 'figure'),
              [Input('updateTwitterGraph', 'n_intervals'), Input('showCumulation', 'n_clicks')],
              [State('termInput', 'value')])
def updateCumulation(n_intervals, n_clicks, term):
    print('updateCumulation')
    if n_intervals != 0 and n_clicks != 0:
        try:
            if os.stat('data.txt').st_size != 0:
                data = getDataMeta()
                x, y = getCumulativeData(data)
                x2, y2 = getTweetsPerSecondData(x, y, 5)
                print('drawing')
                return createFigure([[x,y], [x2,y2]], ['TWITTER DATA', 'TIME', 'VOLUME', 'TWEET PER SECOND'], 500, [])
        except Exception as e:
            print('error occured generating cumulation data')
            print(e)

@app.callback(Output('stockPriceGraph', 'figure'),
              [Input('tickerSubmit', 'n_clicks'), Input(
                  'updateStockGraph', 'n_intervals')],
              [State('tickerInput', 'value'), State('stockTimeRange', 'value')])
def updateStockGraph(n_clicks, n_intervals, ticker, timeRange):
    print('updateStockGraph')
    if n_clicks != 0:
        try:
            ticker = ticker.upper()
            x, y = getStockDayData(ticker, timeRange)
            return createFigure([[x, y]], ['STOCK PRICE: ' + ticker + ' +0000', 'TIME', 'PRICE'], 500, [])
        except Exception as e:
            print('error occured in updateStockGraph:')
            print(e)


@app.callback(Output('streamBuffer', 'children'),
              [Input('termSubmit', 'n_clicks')],
              [State('termInput', 'value')])
def controlStream(n_clicks, term):
    print('controlStream')
    print(threading.enumerate())
    if n_clicks != 0:
        global miningThread
        miningThread = False
        time.sleep(1)
        if (n_clicks != 0) and (term != ''):
            miningThread = True
            thread = threading.Thread(target=streamData, args=([term]))
            thread.start()
            return
        return

if __name__ == '__main__':
    app.run_server(debug=True)
