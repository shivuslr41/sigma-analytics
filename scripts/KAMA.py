# import pickle
import re
import sys
import time
import pandas as pd
import yfinance as yf
from NitroFE import KaufmanAdaptiveMovingAverage
from NitroFE import RelativeStrengthIndex
import requests

try:
    nifty500_list = pd.read_csv("https://www1.nseindia.com/content/indices/ind_nifty500list.csv")['Symbol'].to_list()
except Exception as e:
    print("Reading nifty500 list failed:\n", e.args)
    print("traces:\n", e.with_traceback())
    exit(1)

# telegram configs
BOT_TOKEN = ''
CHAT_ID = ''

def send_message(text:str):
    '''sends given text to telegram channel'''
    tele_base_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text='
    tele_base_url+=text
    requests.get(tele_base_url)

breakout_tickers = []
# breakdown_tickers = []
MAX_RETRY = 10
retry = 0
i=0
# nifty500_list = ['ANGELONE']
while i<len(nifty500_list):
    ticker = nifty500_list[i]+'.ns'
    if MAX_RETRY == retry:
        print("max retries attempted, failed process", ticker)
        send_message(f'max retries attempted, failed process at index={i} ticker={ticker}')
        break
    try:
        time.sleep(1)
        i+=1

        # period to get data from, max for full load
        # if previous object is used then 5d
        PERIOD='6mo'
        # index to calc avg from, 0 for full data clac
        # -1 for last index calc based on previous calculated data
        N=0

        # create kaufman object
        ob = KaufmanAdaptiveMovingAverage(kaufman_efficiency_lookback_period=21, kaufman_efficiency_min_periods=1, fast_ema_span=2, slow_ema_span=30)
        rsi_ob = RelativeStrengthIndex(lookback_period=25)
        
        # TODO: save previous objects
        # try:
        #     file_to_read = open(f"pickles/{nifty500_list[i]}.pickle", "rb")
        #     ob = pickle.load(file_to_read)
        # except:
        #     print(f'object file not found for {ticker}, calc on full data')
        # else:
        #     period='5d'
        #     n=-1

        # download tocker data
        df = yf.download(ticker, period=PERIOD)
        df = df.dropna()

        # calc data
        res = ob.fit(df[N:]['Close'], first_fit=True)
        rsi_res = rsi_ob.fit(df[N:]['Close'], first_fit=True)
        
        # check breakout scenario
        if df[-1:]['Close'][0] > res[-1:]['Close'][0]:
            if df[-2:-1]['Close'][0] <= res[-1:]['Close'][0] and \
                df[-1:]['Volume'][0] > df[-2:-1]['Volume'][0] and \
                rsi_res[-1:]['Close'][0] > 50:
                breakout_tickers.append(ticker)
            # continue
        
        # DISABLE breakdown check for now.
        # check breakdown scenario
        # if df[-1:]['Close'][0] < res[-1:]['Close'][0]:
        #     if df[-2:-1]['Close'][0] >= res[-1:]['Close'][0] and \
        #         df[-1:]['Volume'][0] > df[-2:-1]['Volume'][0] and \
        #         rsi_res[-1:]['Close'][0] < 50:
        #         breakdown_tickers.append(ticker)
        #     continue
       
    except Exception as e:
        print(f"msgs:\n: {e.args}")
        print(f"traces:\n: {e.with_traceback()}")
        retry += 1
        # retry same ticker
        i-=1
        time.sleep(10)
        continue

for idx, t in enumerate(breakout_tickers):
    print('KAMA breakouts -> ', t)
    breakout_tickers[idx] = re.sub('[^a-zA-Z0-9\n\.]', ' ', t)

# for idx, t in enumerate(breakdown_tickers):
#     print('KAMA breakdowns -> ', t)
#     breakdown_tickers[idx] = re.sub('[^a-zA-Z0-9\n\.]', ' ', t)

if retry == MAX_RETRY:
    sys.exit(0)

breakout_msg = 'KAMA breakouts -> '
breakout_tickers_str = ' || '.join(breakout_tickers)
breakout_msg+=breakout_tickers_str
send_message(breakout_msg)

# # just to avoid rate limit errors
# time.sleep(1)

# breakdown_msg = 'KAMA breakdowns -> '
# breakdown_tickers_str = ' || '.join(breakdown_tickers)
# breakout_msg+=breakdown_tickers_str
# send_message(breakout_msg)
