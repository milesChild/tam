import yfinance as yf
import math
import numpy as np
from datetime import timedelta, datetime
import logging

logger = logging.getLogger(__name__)

def get_risk_params(ticker, identifier, sector):
    if sector.lower() in ["equity", "curncy", "crypto"]:
        if sector.lower() == "curncy":
            ticker = ticker + "=X"

        symbol = yf.Ticker(ticker)
        info = symbol.info
        logger.debug(f"Risk param lookup {ticker} {identifier} {sector} {info}")
        try:
            bid = info['bid']
            ask = info['ask']
            midpoint = (bid + ask) / 2
        except Exception as e:
            midpoint = info['previousClose']

        adv = info['averageDailyVolume10Day']

        hist = symbol.history(period="1mo").reset_index()
        residuals = hist["Close"].pct_change(1).dropna() ** 2
        vol = np.sqrt(np.sum(residuals) / len(residuals))
        daily_expected_move = vol * midpoint

    elif sector.lower() in ["corp", "govt"]:
        # need another source to compute bond prices and adv and vol
        # identifier will be more useful here than cusip
        pass

    return bid, ask, adv, midpoint, daily_expected_move
