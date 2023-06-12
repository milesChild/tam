import config as cfg
from util import rds
import yfinance as yf
import pandas as pd
import time
import logging
from typing import List

logger = logging.getLogger(__name__)


def collect_history(ticker_list: List[str] = None, period: str = 'max'):
    '''

    Collects history from Yahoo Finance
    :param ticker_list: list of tickers
    :param period: time period, assumes the entire period (max) or a handful of days (e.g., '5d')
    :return:
    '''
    for symbol in ticker_list:
        logger.error(f"Working on retrieving {symbol}")
        sym = yf.Ticker(symbol)
        hist = sym.history(period=period).reset_index()

        if not hist.empty:
            hist.columns = [i.lower().replace(' ', '_') for i in hist.columns]
            hist['symbol'] = symbol
            print(hist)
            try:
                rds.upsert(**cfg.hibiscus_db, table='px', data=hist)

            except Exception as e:
                logging.error(
                    f'Error in inserting yahoo data from {symbol}; skipping for now - {str(e.args)}')
        else:
            logging.error(f'{symbol} data is empty; nothing to insert')

        # allow for yahoo backoff
        time.sleep(3)


def get_etfs():
    df = pd.read_excel('files/NYSE_Arca_Equities_LMM_Current.xlsx')
    collect_history(df['Symbol'], '3mo')

def get_fx():
    fx = ["USDCAD=X", "EURJPY=X", "EURUSD=X", "EURCHF=X", "USDCHF=X", "EURGBP=X",
    "GBPUSD=X", "AUDCAD=X", "NZDUSD=X", "GBPCHF=X", "AUDUSD=X", "GBPJPY=X", "USDJPY=X",
    "CHFJPY=X", "EURCAD=X", "AUDJPY=X", "EURAUD=X", "AUDNZD=X"]
    collect_history(fx, '3mo')

def get_futures():
    # k: v is yahoo mapping to cme mapping for expiration months (not used now but maybe future)
    FUTURES_MAPPING = {
        'F': 'M'
    }

    df = pd.read_excel('files/CMEExport.xlsx')
    df['Volume'] = df['Volume'].apply(lambda x: int(x.replace(',', '')))
    df = df[(df['Volume'] > 0) & (df['Cleared As'] == 'Futures')].sort_values(by='Exchange')
    ysym = [f"{i}=F" for i in df['Globex']]

    collect_history(ysym, '3mo')

if __name__ == '__main__':
    get_futures()
