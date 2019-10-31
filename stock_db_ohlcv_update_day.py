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


def get_market_ohlcv_by_oneday(date):

    # MKD30030 'KRX의 상장종목검색'을 이용한다.
    
    the_otp_input = {
        'name': 'fileDown',
        'filetype': 'csv',
        'url': 'MKD/04/0406/04060200/mkd04060200',
        'market_gubun': 'ALL',
        'indx_ind_cd': '',
        'sect_tp_cd': 'ALL',
        'isu_cdnm': '',
        'isu_cd': '',
        'isu_nm': '',
        'isu_srt_cd': '',
        'secugrp': 'ST',  # ST, EF, EW, EN, Y
        'stock_gubun': 'on',
        'schdate': date,
        'pagePath': '/contents/MKD/04/0406/04060200/MKD04060200',   #.jsp
    }    
            
    the_otp_url = 'http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx'
    the_download_url = 'http://file.krx.co.kr/download.jspx'

    my_request = requests.post(the_otp_url, the_otp_input)
    otp_code = my_request.content    

    my_download_input = {'code': otp_code}
    my_http_headers = {'Referer': 'http://marketdata.krx.co.kr' + the_otp_input['pagePath']}
    my_request = requests.post(the_download_url, my_download_input, headers=my_http_headers)
    df = pd.read_csv(io.BytesIO(my_request.content), index_col='종목코드')

    df = df[['시가','고가','저가','현재가','거래량(주)','상장주식수(주)','상장시가총액(원)']]
    df.columns = ['시가', '고가', '저가', '종가', '거래량', '주식수', '시가총액']
    df = df.replace('/', '', regex=True)
    df = df.replace(',', '', regex=True)
    df = df.astype(np.int64) # 자료형 개선 필요
    df.reset_index(inplace=True)
    df['시가총액'] = round(df['시가총액'] / 1000000,0).astype(np.int64)
    df['날짜'] = pd.to_datetime(date)
    df['날짜'] = df['날짜'].astype(np.str)
    df['종목코드'] = 'A' + df['종목코드'] # 종목코드 앞에 A추가
    df = df[['날짜', '종목코드', '시가', '고가', '저가', '종가', '거래량', '시가총액', '주식수']]
    # 거래정지종목 시세의 0값은 어떻게 처리?    

    print(date, df.shape)

    return df

def update_db_stock_day(start_date, end_date):

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

    day_list = pd.date_range(start_date, end_date)
    for day in day_list:

        date = day.strftime('%Y%m%d')
        df_local = get_market_ohlcv_by_oneday(date)
        time.sleep(1)        
        df_kospi = pd.merge(df_local, df_kospi_list['code'], left_on='종목코드', right_on='code', how='inner').drop(['code'],axis=1)
        df_kosdaq = pd.merge(df_local, df_kosdaq_list['code'], left_on='종목코드', right_on='code', how='inner').drop(['code'],axis=1)

        try:           
            cur.executemany(query1, df_kospi.values.tolist())
            cur.executemany(query2, df_kosdaq.values.tolist())
            conn.commit()
        except Exception as e:
            print('save_db() 에러발생')
            print(e)

    cur.close()
    conn.close()
    
    print("update_db_stock_day 완료")



if __name__=='__main__': 

    
    # 매일 실행되는 시퀀스는 처리시간을 최소한으로 해야한다.
    # 종목테이블수집, 일별시세수집 10분내로 진행하도록
    # 머신러닝 모델처리 외 타알고리즘 계산이 필요한것들은 개당 1분내에

    start = timeit.default_timer()

    now_time = datetime.date.today().strftime('%Y%m%d')
    # 전 종목 시세 업데이트, 하루단위
    update_db_stock_day(start_date='20191007', end_date=now_time)
    
    stop = timeit.default_timer()    
    print("Time: ", stop-start)



