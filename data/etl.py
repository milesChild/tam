import pandas as pd
import logging
import config as cfg
from ..util import rds

logger = logging.getLogger(__name__)

def dump_bds() -> bool:
    df = pd.read_csv('files/BrokerDealers.csv').rename(columns={'Address': 'address1'})

    try:
        rds.insert(**cfg.hibiscus_db, db='hibiscus', table='counterparty', df=df)
        return True
    except:
        return False