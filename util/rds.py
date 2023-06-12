import pymysql
from pymysql.cursors import DictCursor
import pandas as pd
import logging
from typing import Union, Dict

logger = logging.getLogger(__name__)


def insert(host: str, user: str, password: str, port: int, db: str, table: str, data: Union[pd.DataFrame, Dict]):
    # clean up
    if isinstance(data, pd.DataFrame):
        data.columns = [i.lower() for i in data.columns]
        data = data.astype(object).where(pd.notnull(data), None)

        columns = [f"`{i}`" for i in data.columns]
        values = ','.join(['%s'] * len(columns))
        items = data.values.tolist()
    elif isinstance(data, dict):
        columns = [f"`{i}`" for i in data.keys()]
        values = ','.join(['%s'] * len(columns))
        items = [list(data.values())]
    else:
        raise ValueError("You have the wrong types for data - should be dataframe or dictionary")

    query = f"""
    INSERT INTO {db}.{table} 
    ({','.join(columns)}) VALUES ({values})
    """


    connection = pymysql.connect(host=host, user=user, password=password, port=port)
    cursor = connection.cursor(cursor=DictCursor)

    try:
        cursor.executemany(query, items)
        connection.commit()
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cursor.close()
        connection.close()

def upsert(host: str, user: str, password: str, port: int, db: str, table: str, data: Union[pd.DataFrame, Dict]):
    # clean up
    if isinstance(data, pd.DataFrame):
        data.columns = [i.lower() for i in data.columns]
        data = data.astype(object).where(pd.notnull(data), None)

        columns = [f"`{i}`" for i in data.columns]
        values = ','.join(['%s'] * len(columns))
        items = data.values.tolist()
        replace = [f"{i}=VALUES({i})" for i in columns]
    elif isinstance(data, dict):
        columns = [f"`{i}`" for i in data.keys()]
        values = ','.join(['%s'] * len(columns))
        items = [list(data.values())]
        replace = [f"{i}=VALUES({i})" for i in columns]
    else:
        raise ValueError("You have the wrong types for data - should be dataframe or dictionary")

    query = f"""
    INSERT INTO {db}.{table} 
    ({','.join(columns)}) VALUES ({values})
    ON DUPLICATE KEY UPDATE 
    {','.join(replace)}
    """


    connection = pymysql.connect(host=host, user=user, password=password, port=port)
    cursor = connection.cursor(cursor=DictCursor)

    try:
        cursor.executemany(query, items)
        connection.commit()
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cursor.close()
        connection.close()

def run(host: str, user: str, password: str, port: int, query: str, return_dict: bool = False, **kwargs):
    if kwargs.get('db'):
        connection = pymysql.connect(host=host, user=user, password=password, port=port, db=kwargs['db'])
    else:
        connection = pymysql.connect(host=host, user=user, password=password, port=port)

    cursor = connection.cursor(cursor=DictCursor)

    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result if return_dict  else pd.DataFrame(result)
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cursor.close()
        connection.close()

