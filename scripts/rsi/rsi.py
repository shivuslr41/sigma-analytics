import pandas as pd
import yfinance as yf
import time

# read from csv
df = pd.read_csv('rsi.csv')

# convert date column with dd-mm-yyyy format from object to datetime
df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y')

# convert all other columns to string
df[['symbol', 'marketcapname', 'sector']] = df[['symbol', 'marketcapname', 'sector']].astype('category')

# store duplicate count of ticker in seperate column
df['count'] = df['symbol'].map(df['symbol'].value_counts())

# set download flag
download = False

if download:
    # download data for all tickers and store in csv
    # for ticker in ['ADANIENSOL']:
    for ticker in df['symbol'].unique():
        print(ticker)
        tdf = yf.download(f'{ticker}.ns', period='max', interval="1mo", auto_adjust=False)
        tdf.to_csv(f'data/{ticker}.csv', header=False)
        # sleep for avoiding rate limit
        time.sleep(3)
        # exit(0)

    # download NITFYBEES for benchmarking purposes
    ticker = 'NIFTYBEES'
    tdf = yf.download(f'{ticker}.ns', period='max', interval="1mo", auto_adjust=False)
    tdf.to_csv(f'data/{ticker}.csv', header=False)

# final dataset to  store all symbol returns
gaps = ['1mo', '1mo-benchmark', '3mo', '3mo-benchmark', '6mo', '6mo-benchmark', '1y', '1y-benchmark', '3y', '3y-benchmark', '5y', '5y-benchmark', '10y', '10y-benchmark']
fdf = pd.DataFrame(columns=['symbol'] + gaps)

ticker = 'NIFTYBEES'
# read ticker data from data/ with custom header
nfdf = pd.read_csv(f'data/{ticker}.csv', names=['date', 'adj_close', 'close', 'high', 'low', 'open', 'volume'])
# convert date column from object to datetime
nfdf['date'] = pd.to_datetime(nfdf['date'])

def process_dates_and_months(dates, months):
    result = []

    # Loop until one of the lists is empty
    while dates and months:
        # Compare the earliest dates in each list
        if dates[0] < months[0]:
            # Pop the earliest date from dates and add it to result list
            result.append(('buy', dates.pop(0)))
        elif dates[0] == months[0]:
            # Pop the earliest date from months and add it to result
            result.append(('calc', months.pop(0)))
            # Pop the earliest date from dates and add it to result list
            result.append(('buy', dates.pop(0)))
        else:
            # Pop the earliest date from months and add it to result
            result.append(('calc', months.pop(0)))

    # Add any remaining dates from dates or months to result
    for date in dates:
        result.append(('buy', date))
    for month in months:
        result.append(('calc', month))
    
    return result

# for ticker in ['ADANIENSOL']:
for ticker in df['symbol'].unique():
    print("started", ticker)

    # add symbol to the final df
    fdf.loc[len(fdf)] = [ticker] + [None] * (len(fdf.columns) - 1)

    # collect all dates from df for ticker symbol
    dates = df[df['symbol'] == f'{ticker}']['date'].to_list()
    
    # read ticker data from data/ with custom header
    tdf = pd.read_csv(f'data/{ticker}.csv', names=['date', 'adj_close', 'close', 'high', 'low', 'open', 'volume'])
    # convert date column from object to datetime
    tdf['date'] = pd.to_datetime(tdf['date'])

    # months for return calculation
    months = [dates[0] + pd.DateOffset(months=i) for i in [1,3,6,12,36,60,120]]
    # get dates with action tuple
    actions = process_dates_and_months(dates, months)
    # init buy prices and count
    buy_prices = []
    nf_buy_prices = []
    avg_buy = 0.0
    nf_avg_buy = 0.0
    bought_count = 0
    gap_count = 0

    for action, date in actions:
        if date > pd.to_datetime('today'):
            break

        # get close price from tdf for ticker on that month of date
        close = tdf[(tdf['date'].dt.to_period('M') == date.to_period('M'))]['open'].iloc[0]

        # get close price from nfdf for niftybees on that month of date
        nf_close = nfdf[(nfdf['date'].dt.to_period('M') == date.to_period('M'))]['open'].iloc[0]

        if action == 'buy':
            if bought_count == 0:
                bought_count += 1
                buy_prices.append(close)
                avg_buy = close
                nf_buy_prices.append(nf_close)
                nf_avg_buy = nf_close
                continue

            buy_prices.append(close*bought_count)
            nf_buy_prices.append(nf_close*bought_count)
            avg_buy = sum(buy_prices) / (bought_count * 2)
            nf_avg_buy = sum(nf_buy_prices) / (bought_count * 2)
            bought_count = bought_count * 2
        else:
             # calculate profit percentage
            profit_percentage = ((close - avg_buy) / avg_buy) * 100

            # calculate profit percentage of niftybees
            nf_profit_percentage = ((nf_close - nf_avg_buy) / nf_avg_buy) * 100

            # add profit % for in the fdf
            fdf.loc[fdf['symbol'] == ticker, [gaps[gap_count], gaps[gap_count+1]]] = [profit_percentage, nf_profit_percentage]
            gap_count += 2
    
    # print(fdf.head())
    # print(buy_prices, avg_buy)
    # print(nf_buy_prices, nf_avg_buy)
    # print(bought_count)
    # exit(0)
    print("completed", ticker)

fdf.to_csv('returns.csv', index=False)