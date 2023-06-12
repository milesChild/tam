import requests
import os
import logging
import pandas as pd

logger = logging.getLogger(__name__)

openfigi_apikey = os.getenv("X-OPENFIGI-APIKEY")


def get_figi_from_identifier(identifier, **kwargs):
    if kwargs.get('id_type'):
        identifier_type = kwargs.get('id_type')
    else:
        if len(identifier) == 12:
            identifier_type = "ID_ISIN"
        elif len(identifier) == 9:
            identifier_type = "ID_CUSIP"
        elif len(identifier) == 7:
            identifier_type = "ID_SEDOL"
        else:
            identifier_type = "TICKER"

    security = get_mapping(identifier_type, identifier)
    return security


def get_mapping(id_type, value):
    logger.debug(f"{id_type} {value}")
    openfigi_url = 'https://api.openfigi.com/v1/mapping'
    openfigi_headers = {'Content-Type': 'text/json'}
    query = [{'idType': id_type, 'idValue': value}]
    if openfigi_apikey:
        openfigi_headers['X-OPENFIGI-APIKEY'] = openfigi_apikey
    response = requests.post(url=openfigi_url, headers=openfigi_headers,
                             json=query)
    if response.status_code != 200:
        raise Exception('Bad response code {}'.format(
            str(response.status_code)))

    else:
        result = response.json()

    # go down a horrible chain of events:
    result_df = pd.DataFrame(result[0]['data'])
    us = result_df[result_df['exchCode'] == 'US'].copy()
    if us.shape[0]==1:
        return us.to_dict(orient='records')[0]
    else:
        # check to see if it's a future of some sort
        us = result_df[result_df['marketSector'] == 'Index']
        if us.shape[0] == 1:
            return us.to_dict(orient='records')[0]

    if not result[0].get("data"):
        # they gave us a symbol that returned nothing
        pass
    for r in result[0]["data"]:
        if r["marketSector"].lower() in ["curncy", "equity", "index", "corp", "govt", "comdty"]:
            return r
    return None
