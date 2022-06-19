'''scanner for nr777 statergy - run every monday 8 AM IST to make use of this effectively'''
import time
import sys
from datetime import date
from datetime import timedelta
import requests
import yfinance as yf
import pandas as pd

# required date format by yfinance dowload()
DATE_FORMAT = '%Y-%m-%d'
# Get today's date
today = date.today()
print("fetch till date: ", today)
to_date = today.strftime(DATE_FORMAT)
# months ago date
monthsago = today - timedelta(days = 1500)
print("from date: ", monthsago)
from_date= monthsago.strftime(DATE_FORMAT)

# fetch all tickers of nifty 500 index from nse website
try:
    NIFTY500LIST_URL = 'https://www1.nseindia.com/content/indices/ind_nifty500list.csv'
    nifty500_list = pd.read_csv(NIFTY500LIST_URL)['Symbol'].to_list()
except Exception as e:
    print("Reading nifty500 list failed:\n", e.args)
    print("traces:\n", e.with_traceback())
    sys.exit(1)

# telegram configs
BOT_TOKEN = ''
CHAT_ID = ''

def send_message(text:str):
    '''sends given text to telegram channel'''
    tele_base_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text='
    tele_base_url+=text
    requests.get(tele_base_url)

passed_tickers = []
passed_tickers_without_volume = []
MAX_RETRY = 5
retry = int(0)
i=int(0)
# nifty500_list = ['mrpl']
while i<len(nifty500_list):
    ticker = nifty500_list[i]+'.ns'
    if retry == MAX_RETRY:
        print("max retries attempted, failed process at: ", ticker)
        send_message(f'max retries attempted, failed process at index={i} ticker={ticker}')
        break
    try:
        i+=1

        # avoids rate limit
        time.sleep(1)

        # download weekly timeframe data
        df = yf.download(ticker, start=from_date, end=to_date, interval="1wk")
        df = df.dropna()
        df = df.reindex(index=df.index[::-1])

        # Drop first row
        # df.drop(index=df.index[0], axis=0, inplace=True)

        # print(df)

        # atleast 7 rows should be present
        if len(df.index) < 7:
            print('cannot calculate vr777 for due to insufficiant data: ', ticker)
            continue

        # weekly high-low calculation
        week_high = df[:1]['High'][0]
        week_low = df[:1]['Low'][0]
        continue_outer_loop = False
        for j in range(7):
            if week_high-week_low <= df[j+1:j+2]['High'][0]-df[j+1:j+2]['Low'][0]:
                print(df[:1])
                print(df[j+1:j+2])
                print(week_high-week_low, df[j+1:j+2]['High'][0]-df[j+1:j+2]['Low'][0])
                print(f'does not meet week {j+1} condition: {ticker}')
                continue_outer_loop = True
                break
        if continue_outer_loop:
            continue

        week = df[:1]
        # extra weekly price conditions
        if week['Close'][0] <= week['Open'][0]:
            print('does not meet weekly Close>Open condition: ', ticker)
            continue

        if week['Close'][0] <= df[1:2]['Close'][0]:
            print('does not meet weekly Close> week ago Close: ', ticker)
            continue

        # avoids rate limit
        time.sleep(1)

        # monthly price conditions
        mdf = yf.download(ticker, period='3mo', interval="1mo")
        mdf = mdf.dropna()
        mdf = mdf.reindex(index=mdf.index[::-1])

        # Drop first row, ignore currently running candle
        mdf.drop(index=mdf.index[0], axis=0, inplace=True)
        # print(mdf)
        if mdf[1:2]['Close'][0] <= mdf[1:2]['Open'][0]:
            print('does not meet monthly condition: ', ticker)
            continue

        # avoids rate limit
        time.sleep(1)

        # quaterly price condition
        qdf = yf.download(ticker, period='6mo', interval="3mo")
        qdf = qdf.dropna()
        qdf = qdf.reindex(index=qdf.index[::-1])

        # Drop first row, ignore currently running candle
        qdf.drop(index=qdf.index[0], axis=0, inplace=True)
        # print(qdf)
        if len(qdf) < 1:
            print('insufficient data for quaterly condition', ticker)
            continue
        if qdf[1:2]['Close'][0] <= qdf[1:2]['Open'][0]:
            print('does not meet quaterly condition: ', ticker)
            continue

        print(f'{ticker} meets all price conditions')

        # Volume conditions
        if len(df) < 21:
            print('data not sufficiant for weekly Volume conditions', ticker)
            continue

        week_ago_vol = df[1:2]['Volume'][0]
        # print(week_ago_vol)

        if week_ago_vol <= 20000:
            print('does not meet 20k Volume condition:', ticker)
            continue

        # sma conditions
        if len(df) < 51:
            print('data not sufficiant for weekly Volume conditions', ticker)
            continue
        # 20 sma
        sma_20 = pd.Series(df.head(21)['Close'].to_list()).rolling(20).mean().tolist()[20-1]
        # print(sma_20)
        # 50 sma
        sma_50 = pd.Series(df.head(51)['Close'].to_list()).rolling(50).mean().tolist()[50-1]
        # print(sma_50)
        if sma_20 <= sma_50:
            print('does not meet weekly 20>50 sma condition: ', ticker)
            continue

        if len(df) < 201:
            print('data not sufficiant for weekly Volume conditions', ticker)
            continue
        # 200 sma
        sma_200 = pd.Series(df.head(201)['Close'].to_list()).rolling(200).mean().tolist()[200-1]
        # print(sma_200)
        if sma_50 <= sma_200:
            print('does not meet weekly 50>200 sma condition: ', ticker)
            continue

        print(f'{ticker} satisfies till final volume condition')
        passed_tickers_without_volume.append(ticker)

        # 20 weeks vol sma
        sma_20_vol = pd.Series(df.head(21)['Volume'].to_list()).rolling(20).mean().tolist()[20-1]
        # print(sma_20_vol)
        if week_ago_vol <= sma_20_vol:
            print('does not meet sma Volume condition: ', ticker)
            continue

        print(f'{ticker} satisfies all conditions')
        passed_tickers.append(ticker)
    except Exception as e:
        print(f"msgs:\n: {e.args}")
        print(f"traces:\n: {e.with_traceback()}")
        retry += 1
        # retry same ticker after 10 seconds
        i-=1
        time.sleep(10)
        continue

for t in passed_tickers_without_volume:
    print('passed without volume condition -> ', t)

for t in passed_tickers:
    print('passed with all conditions -> ', t)

if retry == MAX_RETRY:
    sys.exit(0)

msg_wo_vol = 'passed without volume condition -> '
tickers_wo_vol = ' <-> '.join(passed_tickers_without_volume)
msg_wo_vol+=tickers_wo_vol
send_message(msg_wo_vol)

# avoids rate limit errors
time.sleep(1)

msg_vol = 'passed with all conditions -> '
tickers_vol = ' <-> '.join(passed_tickers)
msg_vol+=tickers_vol
send_message(msg_vol)
