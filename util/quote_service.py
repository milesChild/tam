from typing import Tuple
import math
import numpy as np
from datetime import datetime, timedelta
from util import rds
from util.pricing_helpers import get_risk_params
import config as cfg
import logging

logger = logging.getLogger(__name__)


def get_quote(quote_dict) -> Tuple[float, float]:
    logger.debug(f"Fetching quote, params {quote_dict}")
    if quote_dict.get("quote_method") == None or quote_dict.get("quote_method").lower() == "risk":
        return _get_risk_quote(quote_dict)
    elif quote_dict.get("quote_method").lower() == "nav":
        pass


def _get_risk_quote(quote_dict):
    logger.info(f"Entering risk quote {quote_dict}")

    quote_dict['bid_quote'], quote_dict['ask_quote'], adv, midpoint, daily_stock_vol_value = get_risk_params(
        quote_dict['ticker'], quote_dict["identifier"], quote_dict["marketSector"])

    if not quote_dict.get("quote_side") or quote_dict.get('quote_side').upper() not in ["BID", "OFFER", "2WAY"]:
        quote_dict["side"] = "2WAY"
    quote_dict["side"] = quote_dict["quote_side"].upper()
    if (not quote_dict.get('quantity')) or quote_dict.get('quantity') == -1:
        quote_dict['quantity'] = 1000  # default value

    expected_impact = (quote_dict["quantity"] / adv) * daily_stock_vol_value

    query = f"""
    SELECT coalesce(sum(CASE WHEN side='SELL' then -1*quantity else quantity end),0) as quantity 
    FROM hibiscus.transactions WHERE figi = '{quote_dict['figi']}' and event_type = 'TRADE'
    """
    logger.debug(f"Position query {query}")

    position = rds.run(**cfg.hibiscus_db, query=query, return_dict=True)
    logger.debug(f"Position result {position}")

    if len(position) > 0:
        position = float(position[0]["quantity"])
    else:
        position = 0
    logger.info(
        f"Generating position {position} {quote_dict.get('quantity')}")
    potential_position = position + quote_dict["quantity"]

    def position_adjustment(x):
        if x > 0:
            return -math.pow(x/(.015*adv), float(1)/3)
        elif x < 0:
            return math.pow(abs(x)/(.015*adv), float(1)/3)
        else:
            return 0

    position_skew_value = (position_adjustment(
        potential_position)/10000)*midpoint
    logger.debug(
        f"Positional skew as {position_skew_value} using midpoint {midpoint}")

    try:
        cpty_sentiment = rds.run(
            **cfg.hibiscus_db, query="SELECT sentiment FROM hibiscus.counterparty WHERE id = '{}'".format(quote_dict.get("cpty_id")), return_dict=True)[0].get("sentiment")
    except Exception as e:
        cpty_sentiment = 0

    cpty_bid_adjustment, cpty_ask_adjustment = cpty_offsets(cpty_sentiment)

    logger.debug(f"""Final bid ask offsets: expected impact:  {expected_impact},
    position skew: {position_skew_value}, cpty bid adjustment: {cpty_bid_adjustment}, 
    cpty ask adjustment: {cpty_ask_adjustment}""")

    quote_dict["bid_offset"] = round(-1*expected_impact+position_skew_value +
                                     cpty_bid_adjustment, 2)
    quote_dict["ask_offset"] = round(expected_impact+position_skew_value +
                                     cpty_ask_adjustment, 2)

    logger.debug(
        f"Exiting risk quote with final quote_dict params of {quote_dict}")


def cpty_offsets(cpty_sentiment: int):
    if cpty_sentiment == 1:
        cpty_bid_adjustment = +0.01
        cpty_ask_adjustment = -0.01
    else:
        cpty_bid_adjustment = -0.00
        cpty_ask_adjustment = +0.00
    return cpty_bid_adjustment, cpty_ask_adjustment
