import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
import django
django.setup()

import pandas as pd
from nameapp.models import StockTable
from django.db import connections

import numpy as np
import FinanceDataReader as fdr
import logging
import timeit



def update_db_stocktable():

    # 참고 : http://kind.krx.co.kr/corpgeneral/listedIssueStatus.do?method=loadInitPage
    # 주권만 불러오기 (스팩, 외국주권, 투자회사, 우선주, 신주인수권증권, ELW, ETF 등 제외) 
    # 약 2200개, (19.8.30기준 코스피 770 /코스닥 1293개)

    df_kospi_list = fdr.StockListing('KOSPI')
    df_kosdaq_list = fdr.StockListing('KOSDAQ')
    print('코스피 ', df_kospi_list.shape[0])
    print('코스닥 ', df_kosdaq_list.shape[0])
   
    # 코스피,코스닥 구분
    df_kospi_list['구분'] = 0
    df_kosdaq_list['구분'] = 1
    df_all = pd.concat([df_kospi_list, df_kosdaq_list], axis=0)

    # 기존 종목테이블을 지운후 실행
    # StockTable record delete all
    StockTable.objects.all().delete()

    # StockTable sql_sequence reset
    # Executing custom SQL directly : https://docs.djangoproject.com/en/2.2/topics/db/sql/
    conn = connections['default']
    sql_query = "UPDATE sqlite_sequence SET seq = '0' WHERE name = 'nameapp_stocktable';"
    with conn.cursor() as cur:
        cur.execute(sql_query)

    for i in range(df_all.shape[0]):
        StockTable(
            code = 'A' + df_all.iloc[i,0], # 종목코드앞에 A추가
            name = df_all.iloc[i,1],
            sector = df_all.iloc[i,2],
            industry = df_all.iloc[i,3],
            #categories = 
            division = df_all.iloc[i,4]).save()

    return print('종목테이블 업데이트 완료')


if __name__ == "__main__":
    
    # ORM사용하여 저장한다.
    # 기존내용을 모두 지운후 저장, 매일 1회 맨처음 실행되어야함.
    # 백업기능 검토 - 2가지
    # (1) 등록날짜, 종목코드, 종목명 / 일별 계속쌓이는 형태, 2년전 정보는 삭제, DB의 크기를 일정하게 유지시킨다.
    # (2) 일자별 상장종목 CSV 생성 -> 의미없음. KRX에서 제공해줌.    
    # DB구조 FK연결? 1:N, N:N ? : Bottom 종목코드,종목명 / Top KRX 산업구분 / Top Naver 산업구분
    
    # 종목테이블 저장

    start = timeit.default_timer()

    update_db_stocktable()
    
    stop = timeit.default_timer()    
    print("Time: ", stop-start)


    
