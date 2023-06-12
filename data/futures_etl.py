import sys
sys.path.append('..')
import requests
import datetime
from typing import List, Dict
import pandas as pd
from util import rds
import config as cfg

# stupid mics
EXCH_MAPPING = {
    'CME': 'XCME',
    'NYMEX': 'XNYM',
    'CBOT': 'XCBT',
    'COMEX': 'XCEC'
}

FINAL_COLUMNS = ['open', 'close', 'high', 'low', 'volume',
                 'quoteCode', 'exchangeCode', 'tradeDate']

def get_data(securities: List[str], exch_code: str, start_date: int = None):
    epochmilli = int(datetime.datetime.strptime(str(start_date), '%Y%m%d').timestamp()*1000)

    CME_URL = f"""http://www.cmegroup.com/CmeWS/mvc/Quotes/FutureContracts/{exch_code}/G?quoteCodes={','.join(securities)}&_={epochmilli}"""
    print(CME_URL)

    resp = requests.get(CME_URL)
    data = resp.json()
    print(data)

    df = pd.DataFrame(data['quotes'])
    df['tradeDate'] = data['tradeDate']
    df = df[FINAL_COLUMNS].rename(columns={'quoteCode':'symbol', 'exchangeCode': 'exchange_code', 'tradeDate': 'date'})

    print(df)
    rds.upsert(**cfg.hibiscus_db, table='px', data=df)

def parse_cme(start_date, end_date, expiration: str = 'M3'):
    start, end = (datetime.datetime.strptime(str(start_date), '%Y%m%d'),
                  datetime.datetime.strptime(str(end_date), '%Y%m%d'))
    delta = datetime.timedelta(days=1)

    while start < end:

        # let's just filter for those with real volume, can't be bothered to making this very robust to error
        df = pd.read_excel('files/CMEExport.xlsx')
        df['Volume'] = df['Volume'].apply(lambda x: int(x.replace(',', '')))
        df = df[(df['Volume']>0) & (df['Cleared As'] == 'Futures')].sort_values(by='Exchange')

        for exch in df['Exchange'].unique():
            group = df[df['Exchange']==exch]['Globex'].tolist()
            mic_code = EXCH_MAPPING.get(exch)
            tickers = [f"{i}{expiration}" for i in group]
            print(group)

            # get_data(tickers, mic_code, start_date)
        start += delta


if __name__ == '__main__':
    parse_cme(20230605, 20230606, 'M3')


