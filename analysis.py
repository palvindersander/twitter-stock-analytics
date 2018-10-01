import ijson
import os
import json
from datetime import datetime
from datetime import timedelta
import numpy
from scipy import stats
#import pandas_datareader.data as web
import pandas as pd
from bs4 import BeautifulSoup
from urllib import request
import tweepy
import threading
import plotly.graph_objs as go


def getKeys():
    mapboxToken = 'pk.eyJ1IjoicGFsdmluZGVyc2FuZGVyIiwiYSI6ImNqanNsOWtjeTg1MzkzcHMycTc2Z25meGYifQ.XphirdAv5UefGIMDeaJrxg'
    twitterCKey = '1b1mWMd7Up88sKceqF2d417hM'
    twitterCSecret = 'ZLM7MwefJmrU30IzpqJFOFoTdGKfppTUN8nWLKDWWIbTetdzuH'
    twitterAToken = '942144532233248769-Ox5l5MCIifUK5mhhFpyVAugrxPkHkN9'
    twitterASecret = '9Ntpl7F8799RgGja9gSAkioiOoFzLsVVhAnYV0m0cZpO4'
    keys = {'mapboxToken': mapboxToken,
            'twitterCKey': twitterCKey,
            'twitterCSecret': twitterCSecret,
            'twitterAToken': twitterAToken,
            'twitterASecret': twitterASecret}
    return keys


def insertionsortData(data):
    for i in range(1, len(data)):
        currentValue = data[i]
        x = i
        while x > 0 and parseStatusDate(data[x - 1]['created_at']) > parseStatusDate(currentValue['created_at']):
            data[x] = data[x - 1]
            x = x - 1
        data[x] = currentValue
    return data


def simplifyData():
    x = []
    f = open("data.txt", 'r')
    objects = ijson.items(f, 'item')
    count = 0
    for tweet in objects:
        status = json.loads(tweet)
        print(count + 1)
        count = count + 1
        x.append({'created_at': status['created_at'],
                  'coordinates': status['coordinates'], 'geo': status['geo']})
    f.close()
    return x


def getDataMeta():
    data = []
    statinfo = os.stat('data.txt')
    if statinfo.st_size > 100000000:
        data = simplifyData()
    else:
        with open('data.txt') as statusFile:
            tweets = json.load(statusFile)
            for i in range(0, len(tweets)):
                tweet = json.loads(tweets[i])
                data.append(tweet)
            statusFile.close()
    '''with open('meta.txt', 'r') as metaFile:
        meta = str(metaFile.read())
        metaFile.close()'''
    # return insertionsortData(data), meta
    return insertionsortData(data)


def getGeoData(data):
    lat = []
    lon = []
    text = []
    for status in data:
        if status['coordinates'] is not None:
            latitude = status['geo']['coordinates'][0]
            longitude = status['geo']['coordinates'][1]
            lat.append(latitude)
            lon.append(longitude)
            text.append(str(latitude) + ', ' + str(longitude))
    return lat, lon, text


def getStockDayDataredundancy(ticker, timeRange):
    df = web.DataReader(ticker, 'iex',
                        timeRange[0],
                        timeRange[1]).reset_index()
    return df


def getStockDayData(ticker, period):
    link = 'https://api.iextrading.com/1.0/stock/' + \
        ticker.upper() + '/chart/' + period + '?format=csv'
    data = pd.read_csv(link)

    if period == '1d':
        x = []
        for date in data.iloc[:, 0]:
            for time in data.iloc[:, 1]:
                date = str(date)
                time = str(time)
                year = int(date[0:4])
                if date[5] == '0':
                    month = int(date[6])
                else:
                    month = int(date[5:6])
                if date[7] == '0':
                    day = int(date[8])
                else:
                    day = int(date[7:8])
                if time[0] == '0':
                    hour = int(time[1])
                else:
                    hour = int(time[0:2])
                if time[3] == '0':
                    min = int(time[4])
                else:
                    min = int(time[3:5])
                dateobj = datetime(year, month, day, hour,
                                   min, 0) + timedelta(hours=5)
                x.append(dateobj)
        y = []
        for price in data.iloc[:, 5]:
            if price != -1:
                y.append(float(price))
            else:
                index = len(y)
                del x[index]

    else:
        x = []
        for date in data.iloc[:, 0]:
            date = str(date)
            year = int(date[0:4])
            if date[5] == '0':
                month = int(date[6])
            else:
                month = int(date[5:7])
            if date[8] == '0':
                day = int(date[9])
            else:
                day = int(date[8:10])
            dateobj = datetime(year, month, day, 0, 0, 0)
            x.append(dateobj)
        y = []
        for price in data.iloc[:, 4]:
            if price != -1:
                y.append(float(price))
            else:
                index = len(y)
                del x[index]

    return x, y


def parseStatusDate(date):
    date = date.split(' ')
    del (date[4])
    del (date[0])
    date.insert(2, date.pop(3))
    dateStr = str(date[0]) + ' ' + str(date[1]) + ' ' + \
        str(date[2]) + ' ' + str(date[3])
    dateTimeObject = datetime.strptime(dateStr, '%b %d %Y %H:%M:%S')
    return dateTimeObject


def getCumulativeData(data):
    x = []
    y = []
    tweetNumber = 0
    index = 0
    while index < (len(data)):
        date = parseStatusDate(data[index]['created_at'])
        count = index
        while (count != (len(data) - 1)) and (str(date) == str(parseStatusDate(data[count + 1]['created_at']))):
            count = count + 1
        valuesAccounted = (count - index) + 1
        tweetNumber = tweetNumber + valuesAccounted
        x.append(date)
        y.append(tweetNumber)
        if index != count:
            index = count + 1
        else:
            index = index + 1
    return x, y


def getTweetsPerSecondData(a, b, interval):
    o = []
    p = []
    lower = a[0] + timedelta(seconds=interval)
    index = 0
    o.append(a[0])
    p.append(b[0])
    while index < len(a) - 1:
        if (a[index] <= lower) and (a[index + 1] > lower) and (a[index] != o[0]):
            lower = lower + timedelta(seconds=interval)
            o.append(a[index])
            p.append(b[index])
        elif (a[index] > lower) and (o[-1] == a[index - 1]):
            lower = lower + timedelta(seconds=interval)
            o.append(a[index])
            p.append(b[index])
        index = index + 1
    o.append(a[-1])
    p.append(b[-1])
    x = []
    y = []
    for i in range(1, len(o)):
        realInterval = o[i] - o[i - 1]
        realInterval = realInterval.seconds
        tweetsPerSecond = (p[i] - p[i - 1]) / realInterval
        y.append(tweetsPerSecond)
        x.append(o[i])
    return x, y


def getCorrelation(x, y, timeRange):
    if timeRange is None:
        arbitraryDate = datetime(2018, 1, 1)
        dates = numpy.array([(i - arbitraryDate).total_seconds() for i in x])
        pearson = stats.pearsonr(dates, y)
        return pearson
    else:
        lowerBound = timeRange[0]
        upperBound = timeRange[1]
        a = []
        b = []
        a.append(x[0])
        b.append(y[0])
        loop = True
        index = lowerBound
        while (index < len(x) - 1) and (loop == True):
            if (x[index] <= x[upperBound]) and (x[index + 1] > x[upperBound]):
                loop = False
            else:
                a.append(x[index])
                b.append(y[index])
            index = index + 1
        arbitraryDate = datetime(2018, 1, 1)
        dates = numpy.array([(i - arbitraryDate).total_seconds() for i in a])
        pearson = stats.pearsonr(dates, b)
        return pearson


def getColorScheme(scheme):
    light = {
        'background': '#FFF',
        'text': '#000',
        'map': 'light'
    }
    dark = {
        'background': '#000',
        'text': '#FFF',
        'map': 'dark'
    }
    if scheme.lower() == 'dark':
        return dark
    elif scheme.lower() == 'light':
        return light


def getPrice(ticker):
    link = 'https://finance.yahoo.com/quote/' + ticker.upper() + '/'
    page = request.urlopen(link)
    soup = BeautifulSoup(page, 'html.parser')
    price_box = soup.find('span', attrs={'class': 'Trsdu(0.3s)'})
    price = price_box.text.strip()
    return price


def createFigure(dataset, titles, height, range):
    scatterData = []

    for data in dataset:
        scatter = go.Scatter(
            x=data[0],
            y=data[1],
            mode='lines',
            opacity=0.7,
            marker={
                'size': 2,
            },
            line=dict(
                shape='linear',
            ),
            name=titles[dataset.index(data)+2],
            yaxis='y'+str(dataset.index(data)+1)
        )
        scatterData.append(scatter)

    if range == []:
        if len(dataset) == 2:
            layout = go.Layout(
                title=titles[0],
                height=height,
                xaxis=dict(
                    title=titles[1],
                ),
                yaxis=dict(
                    title=titles[2],
                ),
                yaxis2=dict(
                    title=titles[3],
                    overlaying='y',
                    side='right'
                ),
            )
        else:
            layout = go.Layout(
                title=titles[0],
                height=height,
                xaxis=dict(
                    title=titles[1],
                ),
                yaxis=dict(
                    title=titles[2],
                ),
            )
    else:
        if len(dataset) == 2:
            layout = go.Layout(
                title=titles[0],
                height=height,
                xaxis=dict(
                    title=titles[1],
                    range=[range[0], range[1]]
                ),
                yaxis=dict(
                    title=titles[2],
                ),
                yaxis2=dict(
                    title=titles[3],
                    overlaying='y',
                    side='right'
                ),
            )
        else:
            layout = go.Layout(
                title=titles[0],
                height=height,
                xaxis=dict(
                    title=titles[1],
                    range=[range[0], range[1]]
                ),
                yaxis=dict(
                    title=titles[2],
                ),
            )
    figure = {'data': scatterData, 'layout': layout}
    return figure
