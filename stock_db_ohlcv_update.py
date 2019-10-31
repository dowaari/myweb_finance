import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
import django
django.setup()

from nameapp.models import StockTable, Kospi, Kosdaq
from django_pandas.io import read_frame

import pandas as pd
import numpy as np
import sqlite3
import FinanceDataReader as fdr
import time
import io
import requests
import datetime
import logging
import timeit

# pykrx
from pykrx.website.comm import dataframe_empty_handler
from pykrx.website.krx.market.core import MKD30040
from pykrx.website.krx.market.ticker import get_stock_ticker_isin


@dataframe_empty_handler
def get_market_ohlcv_by_date_extend(fromdate, todate, ticker):

    isin = get_stock_ticker_isin(ticker) # '005930'-> 'KR7005930003'반환
    df = MKD30040().read(fromdate, todate, isin)
    # df empty일시 dataframe_empty_handler가 처리

    df = df[['trd_dd', 'tdd_opnprc', 'tdd_hgprc', 'tdd_lwprc',
             'tdd_clsprc', 'acc_trdvol', 'mktcap', 'list_shrs']]
    df.columns = ['날짜', '시가', '고가', '저가', '종가', '거래량', '시가총액', '주식수']
    df = df.replace('/', '', regex=True)
    df = df.replace(',', '', regex=True)
    df = df.set_index('날짜')
    df = df.astype(np.int64) # 자료형 개선 필요
    df.reset_index(inplace=True)
    df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d').astype(np.str)
    df['종목코드'] = 'A' + ticker # 종목코드 앞에 A추가
    df = df[['날짜', '종목코드', '시가', '고가', '저가', '종가', '거래량', '시가총액', '주식수']]

    print('krx', ticker, df.shape)
    
    return df

@dataframe_empty_handler
def get_market_ohlcv_by_date_naver(fromdate, todate, ticker):

    df = fdr.DataReader(ticker, fromdate, todate)
    
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.columns = ['시가', '고가', '저가', '종가', '거래량']    
    df = df.astype(np.int64) # 자료형 개선 필요
    df.reset_index(inplace=True)
    df['날짜'] = pd.to_datetime(df['Date'], format='%Y%m%d').astype(np.str)
    df['종목코드'] = 'A' + ticker # 종목코드 앞에 A추가
    df = df[['날짜', '종목코드', '시가', '고가', '저가', '종가', '거래량']]

    print('naver', ticker, df.shape)
    
    return df


def update_db_stock(start_date, end_date, adjusted=False):

    # 종목테이블 DB에 있는 종목만 저장한다.
    kospi_list = StockTable.objects.filter(division=0)
    kosdaq_list = StockTable.objects.filter(division=1)
    df_kospi_list  = read_frame(kospi_list, fieldnames=['code','name'])
    df_kosdaq_list  = read_frame(kosdaq_list, fieldnames=['code','name'])    
    #print(df_kospi_list.shape, df_kosdaq_list.shape)

    conn = sqlite3.connect('./db.sqlite3')
    cur = conn.cursor()

    query1 = """
    insert or replace into nameapp_kospi(date, code, open, high, low, close, volume,
    total, shares) values(?,?,?,?,?,?,?,?,?) 
    """   
    query2 = """
    insert or replace into nameapp_kosdaq(date, code, open, high, low, close, volume,
    total, shares) values(?,?,?,?,?,?,?,?,?)
    """    

    for ticker in df_kospi_list['code']:
        df_local = get_market_ohlcv_by_date_extend(start_date, end_date, ticker[1:]) # 현재일은 안됨.
        if (adjusted == True) and (df_local.shape[0] > 0): # 수정주가 적용
            df_local_naver = get_market_ohlcv_by_date_naver(start_date, end_date, ticker[1:])
            if df_local_naver.shape[0] > 0:
                df_local = pd.merge(df_local_naver, df_local[['날짜','시가총액','주식수']], on='날짜', how='inner')        
        time.sleep(1)
        try:           
            cur.executemany(query1, df_local.values.tolist())
            conn.commit()
        except Exception as e:
            print('save_db() 에러발생')
            print(e)

    for ticker in df_kosdaq_list['code']:
        df_local = get_market_ohlcv_by_date_extend(start_date, end_date, ticker[1:]) # 현재일은 안됨.
        if (adjusted == True) and (df_local.shape[0] > 0): # 수정주가 적용
            df_local_naver = get_market_ohlcv_by_date_naver(start_date, end_date, ticker[1:])
            if df_local_naver.shape[0] > 0:
                df_local = pd.merge(df_local_naver, df_local[['날짜','시가총액','주식수']], on='날짜', how='inner')
        time.sleep(1)
        try:           
            cur.executemany(query2, df_local.values.tolist())
            conn.commit()
        except Exception as e:
            print('save_db() 에러발생')
            print(e)

  
    cur.close()
    conn.close()
    
    print("update_db_stock 완료")


if __name__=='__main__': 

    start = timeit.default_timer()

    now_time = datetime.date.today().strftime('%Y%m%d')
    # 전 종목 시세 업데이트 (장기) - 테스트중
    update_db_stock(start_date='20190101', end_date=now_time, adjusted=True)
    
    stop = timeit.default_timer()   
    print("Time: ", stop-start)

    # 20190101 ~ 20191030 , 87분 소요