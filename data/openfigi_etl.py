import sys
sys.path.append('..')
from util import rds, openfigi
import config as cfg
import pandas as pd
import time
import logging


logger = logging.getLogger(__name__)

def clean_symbol(val: str) -> str:
    """ Some little light parsing"""
    if val[-2:] == '=F':
        return f"{val[:-2]}M3"
    elif val[-2:] == '=X':
        return f"{val[:-2]}"
    else:
        return val

def enrich_px():
    """Enriches yahoo px symbols and tws identifiers with figi if available"""
    query = """
    select symbol from hibiscus.px
    where figi is null
    """

    df = rds.run(**cfg.hibiscus_db, query=query)

    if not df.empty:
        df['clean_symbol'] = df['symbol'].apply(clean_symbol)

        for i, row in df.iterrows():
            print(i, row['symbol'])
            if row['symbol'][-2:] == '=F':
                id_type = 'ID_FULL_EXCHANGE_SYMBOL'
            else:
                id_type = None

            while True:
                try:
                    val = openfigi.get_figi_from_identifier(row['clean_symbol'], id_type=id_type)
                    break
                except KeyError:
                    val = None
                    break
                except Exception as e:
                    logger.error(f"{e} Trying again")
                    time.sleep(5)

            if val:
                row['figi'] = val['figi']
                rds.upsert(**cfg.hibiscus_db, table='px', data=dict(row))

                result = pd.DataFrame([val])
                rds.upsert(**cfg.hibiscus_db, table='figi', data=result)
            time.sleep(1)

enrich_px()