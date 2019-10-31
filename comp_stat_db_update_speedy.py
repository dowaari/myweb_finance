import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
## Python이 실행될 때 DJANGO_SETTINGS_MODULE이라는 환경 변수에 현재 프로젝트의 settings.py파일 경로를 등록합니다.
## 이제 장고를 가져와 장고 프로젝트를 사용할 수 있도록 환경을 만듭니다.
import django
django.setup()

import pandas as pd
from nameapp.models import CompanyStat, CompanyExtr
from django.db import IntegrityError

import numpy as np
import sqlite3
import FinanceDataReader as fdr
import time
import requests
from bs4 import BeautifulSoup
import re
import datetime
from datetime import timedelta, datetime
import urllib.request
from http.cookiejar import CookieJar
import logging


# https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

def get_webpage(url, encoding=""):
    
    cj = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95  Safari/537.36')]

    respstr = ""
    try:
        op = opener.open(url)
        sourcecode = op.read()
    except Exception as e:
        time.sleep(1)
        op = opener.open(url)
        sourcecode = op.read()

    encodingmethod = op.info().get_param('charset')
    if encodingmethod == None:
        if encoding != "":
            encodingmethod = encoding

    if encoding != "":
        encodingmethod = encoding

    try:
        respstr = sourcecode.decode(encoding=encodingmethod, errors='ignore')
    except Exception as e:
        respstr = sourcecode.decode(encoding="cp949", errors='ignore')

    opener.close()

    return respstr


# BeautifulSoup -> 특정테이블 입력 -> 특정위치tr,td에서 값을 가져와 Dataframe형식으로 반환
def get_data_from_table_itooza(target_table):

    df_local = None
    result = []
    drop_record_list = [] 
    
    for tr in target_table.find_all('tr'):
        for th in tr.find_all('th'): # 컬럼           
            value = '20'+"%s" % th.text[:-1].replace('.','-').strip()
            if ('-02' in value):
                value = value + '-28'
            elif ('-04' in value) or ('-06' in value) or ('-09' in value) or ('-11' in value):
                value = value + '-30'
            elif ('-01' in value) or ('-03' in value) or ('-05' in value) or ('-07' in value) or ('-08' in value) or ('-10' in value) or ('-12' in value):
                value = value + '-31'
            result.append(value)
        # 값
        for td in tr.find_all('td'): # 행
            value = td.text.strip().replace(',','')
            try:
                value = float(value)
            except:
                value = np.NaN
            result.append(value)

    #result = result[1:]
    dfdata = []

    for x in range(0, len(result), 13):    
        dfdata.append(result[x:x+13])

    df_local = pd.DataFrame(data=dfdata).T
    df_local.columns= df_local.iloc[0]
    df_local.drop(df_local.index[0], axis=0, inplace=True)
    df_local = df_local.infer_objects() # convert_objects(convert_numeric=True)

    ######### 모두 Null이면 해당 레코드 제외하기, 날짜와 주가 제외
    for i in range(df_local.shape[0]):    
        if df_local.iloc[i,1:-1].isnull().sum() >= (df_local.shape[1]-2): # Null의 갯수
            drop_record_list.append(i+1)
    df_local.drop(drop_record_list, axis=0, inplace =True)
    
    return df_local 


# BeautifulSoup -> 특정테이블 입력 -> 특정위치tr,td에서 값을 가져와 Dataframe형식으로 반환
def get_data_from_table_fnguide(target_table):
    
    df_local = None
    result = []
    drop_record_list = [] 

    for tr in target_table.find_all('tr'):
        for th in tr.find_all('th'): # 컬럼           
            value = "%s" % th.text.replace('(P) : Provisional','').replace('(E) : Estimate','').replace('잠정실적','').replace('컨센서스, 추정치','').replace('(E)','').replace('(P)','').replace('/','-').strip()
            if ('-02' in value):
                value = value + '-28'
            elif ('-04' in value) or ('-06' in value) or ('-09' in value) or ('-11' in value):
                value = value + '-30'
            elif ('-01' in value) or ('-03' in value) or ('-05' in value) or ('-07' in value) or ('-08' in value) or ('-10' in value) or ('-12' in value):
                value = value + '-31'
            result.append(value)
        # 값
        for td in tr.find_all('td'): # 행
            value = td.text.strip().replace(',','')
            try:
                value = float(value)
            except:
                value = np.NaN
            result.append(value)

    result = result[1:]
    dfdata = []

    for x in range(0, len(result), 9):    
        dfdata.append(result[x:x+9])
    
    df_local = pd.DataFrame(data=dfdata).T
    df_local.columns= df_local.iloc[0]
    df_local.drop(df_local.index[0], axis=0, inplace=True)
    df_local = df_local.infer_objects() # convert_objects(convert_numeric=True)

    ######### 모두 Null이면 해당 레코드 제외하기 , 날짜제외
    for i in range(df_local.shape[0]):    
        if df_local.iloc[i,1:].isnull().sum() >= (df_local.shape[1]-1): # Null의 갯수
            drop_record_list.append(i+1)
    df_local.drop(drop_record_list, axis=0, inplace =True)
    
    return df_local 


# 종목코드에 해당하는 테이블 2개 (연간지표, 분기지표) 데이터프레임으로 반환
def get_company_jaemu_itooza(code): 
    
    url= 'http://search.itooza.com/index.htm?seName=%s' % (code)
    code = 'A'+ code
    
    respstr = get_webpage(url, encoding="euc-kr")
    time.sleep(0.3)
#     handle_b= urllib.request.urlopen(url_b).read()
#     html_b = handle_b.decode('euc-kr','replace').encode('utf-8','replace')
#     soup_b = BeautifulSoup(html_b, 'html.parser')
    soup = BeautifulSoup(respstr, "lxml")

    # 테이블 구분, html에서 테이블의 위치
    gubun_list = ['indexTable2', 'indexTable3'] 
    # 칼럼형식
    column1 = ['날짜','EPS연결', 'EPS개별', 'PER', 'BPS', 'PBR',
               'DPS', '배당수익률', 'ROE', '순이익률', '영업이익률', '주가']
  
    for gubun in gubun_list:        
        try:
            target_table = soup.find_all("div", id=gubun)[0].find('table')

            if gubun == 'indexTable2': # df_연간
                df_cyr = get_data_from_table_itooza(target_table) # 테이블을 데이터프레임으로 반환
                df_cyr.columns = column1 # 칼럼을 일관되게
                df_cyr['날짜'] = pd.to_datetime(df_cyr['날짜']) # 날짜를 datetime형식으로

            elif gubun == 'indexTable3': # df_분기          
                df_cqt = get_data_from_table_itooza(target_table)
                df_cqt.columns = column1
                df_cqt['날짜'] = pd.to_datetime(df_cqt['날짜'])
                
        except: 
            logger.info('%s %s 테이블 가져오기 실패' % (code, gubun))
            # 테이블 가져오기 실패시 레코드가 없는 빈 데이터프레임을 반환
            if gubun == 'indexTable2':
                df_cyr = pd.DataFrame(columns=column1) 
            if gubun == 'indexTable3':
                df_cqt = pd.DataFrame(columns=column1)          
            continue    
    
    df_cyr['code'] = code # 마지막에 종목코드 칼럼추가
    df_cqt['code'] = code    
    
    return (df_cyr, df_cqt) 


# 종목코드에 해당하는 테이블 4개 (연결연간, 연결분기, 개별연간, 개별분기) 데이터프레임으로 반환
def get_company_jaemu_fnguide(code):
        
    code = 'A'+ code # fnguide의 경우 코드앞에 A 붙인다.
    url = "http://asp01.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=%s&NewMenuID=11&cID=50&MenuYn=N" % (code)
    respstr = get_webpage(url, encoding="utf8")
#     response = requests.get(url)
#     respstr = response.text       
    time.sleep(0.3)
    soup = BeautifulSoup(respstr, "lxml")
 
    # 테이블 구분, html에서 테이블의 위치
    gubun_list = ['highlight_D_Y', 'highlight_D_Q', 'highlight_B_Y', 'highlight_B_Q'] 
    # 연결테이블의 칼럼형식
    column1 = ['날짜','매출액', '영업이익', '당기순이익', '지배순이익', '비지배순이익',
               '자산총계', '부채총계', '자본총계', '지배지분', '비지배지분',
               '자본금', '부채비율', '유보율', '영업이익률', '순이익률',
               'ROA', 'ROE', 'EPS', 'BPS', 'DPS', 'PER', 'PBR', '발행주식수', '배당수익률']
    # 개별테이블의 칼럼형식
    column2 = ['날짜','매출액', '영업이익', '당기순이익',
               '자산총계', '부채총계', '자본총계', 
               '자본금', '부채비율', '유보율', '영업이익률', '순이익률',
               'ROA', 'ROE', 'EPS', 'BPS', 'DPS', 'PER', 'PBR', '발행주식수', '배당수익률']
    
    for gubun in gubun_list: 
        
        try:
            target_table = soup.find("div", class_="um_table", id=gubun)

            if gubun == 'highlight_D_Y': # df_연결연간
                df_cyr = get_data_from_table_fnguide(target_table) # 테이블을 데이터프레임으로 반환
                df_cyr.columns = column1 # 칼럼을 일관되게
                df_cyr['날짜'] = pd.to_datetime(df_cyr['날짜']) # 날짜를 datetime형식으로

            elif gubun == 'highlight_D_Q': # df_연결분기          
                df_cqt = get_data_from_table_fnguide(target_table)
                df_cqt.columns = column1
                df_cqt['날짜'] = pd.to_datetime(df_cqt['날짜'])

            elif gubun == 'highlight_B_Y': # df_개별연간  
                df_byr = get_data_from_table_fnguide(target_table)
                df_byr.columns = column2
                df_byr['날짜'] = pd.to_datetime(df_byr['날짜'])

            elif gubun == 'highlight_B_Q': # df_개별분기 
                df_bqt = get_data_from_table_fnguide(target_table)
                df_bqt.columns = column2
                df_bqt['날짜'] = pd.to_datetime(df_bqt['날짜']) 
                
        except: 
            logger.info('%s %s 테이블 가져오기 실패' % (code, gubun))
            # 테이블 가져오기 실패시 레코드가 없는 빈 데이터프레임을 반환
            if gubun == 'highlight_D_Y':
                df_cyr = pd.DataFrame(columns=column1) 
            if gubun == 'highlight_D_Q':
                df_cqt = pd.DataFrame(columns=column1)
            if gubun == 'highlight_B_Y':
                df_byr = pd.DataFrame(columns=column2)
            if gubun == 'highlight_B_Q':
                df_bqt = pd.DataFrame(columns=column2)            
            continue    
    
    df_cyr['code'] = code # 마지막에 종목코드 칼럼추가
    df_cqt['code'] = code
    df_byr['code'] = code
    df_bqt['code'] = code
    
    return (df_cyr, df_cqt, df_byr, df_bqt)
    

def save_db(table_name, df_local):

# (1) Create connection
# (2) Create cursor
# (3) Create Query string
# (4) Execute the query
# (5) Commit to the query
# (6) Close the cursor
# (7) Close the connection

# conn= sqlite3.connect('./data/StockData3.sqlite')
# cur = conn.cursor()
# query= "INSERT INTO tablename (column1, column2) VALUES (?, ?)"
# cursor.execute(query, (value1, value2))
# conn.commit()
# cur.close()
# conn.close()

# with sqlite3.connect('./data/StockData3.sqlite') as conn:
#     cur = conn.cursor()
#     query = "insert or replace into 코스닥_일별주가(종목코드, 날짜, 종가) values(?, ?, ?)"
#     query = "insert or ignore into 코스닥_일별주가(종목코드, 날짜, 종가) values(?, ?, ?)"
#     cur.executemany(query, df.values.tolist())
#     conn.commit()

    return True


# 장고DB에 재무제표를 업데이트 한다. from fnguide
def update_db_companystat(code_list, start_date, end_date):

    conn = sqlite3.connect('./db.sqlite3')
    cur = conn.cursor()

    query1 = """
    insert or ignore into nameapp_companystat(date, sale, profit, netincome, d_netincome, 
    b_netincome, asset, liability, equity, d_equity, b_equity, equity_stock, 
    code, freq, gubun) values(?,?,?,?,?,?,?,?,?,?,?,?,?,'연간','연결')
    """   
    query2 = """
    insert or ignore into nameapp_companystat(date, sale, profit, netincome, d_netincome, 
    b_netincome, asset, liability, equity, d_equity, b_equity, equity_stock, 
    code, freq, gubun) values(?,?,?,?,?,?,?,?,?,?,?,?,?,'분기','연결')
    """   
    query3 = """
    insert or ignore into nameapp_companystat(date, sale, profit, netincome, 
    asset, liability, equity, equity_stock, 
    code, freq, gubun) values(?,?,?,?,?,?,?,?,?,'연간','개별')
    """     
    query4 = """
    insert or ignore into nameapp_companystat(date, sale, profit, netincome, 
    asset, liability, equity, equity_stock, 
    code, freq, gubun) values(?,?,?,?,?,?,?,?,?,'분기','개별')
    """     

    use_col1 = ['날짜','매출액', '영업이익', '당기순이익', '지배순이익', '비지배순이익',
           '자산총계', '부채총계', '자본총계', '지배지분', '비지배지분', '자본금', 'code']
    use_col2 = ['날짜','매출액', '영업이익', '당기순이익',
            '자산총계', '부채총계', '자본총계', '자본금', 'code']

    printProgressBar(0, len(code_list), prefix = 'Progress:', suffix = 'Start', length = 50)  
    for i, code in enumerate(code_list):
        printProgressBar(i+1, len(code_list), prefix = 'Progress:', suffix = 'Complete', length = 50) 

        # 재무데이터를 데이터프레임 형식으로 가져온다. (에러날경우에도 return값 있음.)
        df_연결연간, df_연결분기, df_개별연간, df_개별분기 = get_company_jaemu_fnguide(code)        

        # 기간을 지정할수있다.
        df_연결연간 = df_연결연간[(df_연결연간['날짜'] > start_date) & (df_연결연간['날짜'] < end_date)]
        df_연결분기 = df_연결분기[(df_연결분기['날짜'] > start_date) & (df_연결분기['날짜'] < end_date)]
        df_개별연간 = df_개별연간[(df_개별연간['날짜'] > start_date) & (df_개별연간['날짜'] < end_date)]
        df_개별분기 = df_개별분기[(df_개별분기['날짜'] > start_date) & (df_개별분기['날짜'] < end_date)]    

        df_연결연간['날짜'] = df_연결연간['날짜'].astype(np.str) # 날짜의 형식을 문자열로 변경 (DB저장시 타입오류때문)
        df_연결분기['날짜'] = df_연결분기['날짜'].astype(np.str)
        df_개별연간['날짜'] = df_개별연간['날짜'].astype(np.str)
        df_개별분기['날짜'] = df_개별분기['날짜'].astype(np.str)

        # DB에 저장한다.
        # save_db('연결연간재무', df_연결연간[use_col1])
        # save_db('연결분기재무', df_연결분기[use_col1])
        # save_db('개별연간재무', df_개별연간[use_col2])
        # save_db('개별분기재무', df_개별분기[use_col2])

        try:     
            cur.executemany(query1, df_연결연간[use_col1].values.tolist())
            cur.executemany(query2, df_연결분기[use_col1].values.tolist())
            cur.executemany(query3, df_개별연간[use_col2].values.tolist())
            cur.executemany(query4, df_개별분기[use_col2].values.tolist())
            conn.commit()    
        except Exception as e:
            print('save_db() 에러발생')
            print(e)

    cur.close()
    conn.close()
    
    print("update_db_companystat 완료")
    logger.info("update_db_companystat 완료")


# 장고DB에 투자지표를 업데이트 한다. from itooza
def update_db_companyextr(code_list, start_date, end_date):

    conn = sqlite3.connect('./db.sqlite3')
    cur = conn.cursor()

    query1 = """
    insert or ignore into nameapp_companyextr(date, d_eps, b_eps, per, bps,
    pbr, dps, dps_rate, roe, netincome_rate, profit_rate, price, 
    code, freq) values(?,?,?,?,?,?,?,?,?,?,?,?,?,'연간')
    """   
    query2 = """
    insert or ignore into nameapp_companyextr(date, d_eps, b_eps, per, bps,
    pbr, dps, dps_rate, roe, netincome_rate, profit_rate, price, 
    code, freq) values(?,?,?,?,?,?,?,?,?,?,?,?,?,'분기')
    """   

    printProgressBar(0, len(code_list), prefix = 'Progress:', suffix = 'Start', length = 50)  
    for i, code in enumerate(code_list):
        printProgressBar(i+1, len(code_list), prefix = 'Progress:', suffix = 'Complete', length = 50) 
        
        df_연간지표, df_분기지표 = get_company_jaemu_itooza(code)

        df_연간지표 = df_연간지표[(df_연간지표['날짜'] > start_date) & (df_연간지표['날짜'] < end_date)]
        df_분기지표 = df_분기지표[(df_분기지표['날짜'] > start_date) & (df_분기지표['날짜'] < end_date)]

        df_연간지표['날짜'] = df_연간지표['날짜'].astype(np.str) 
        df_분기지표['날짜'] = df_분기지표['날짜'].astype(np.str)

        # save_db('연간지표', df_연간지표)
        # save_db('분기지표', df_분기지표)

        try:     
            cur.executemany(query1, df_연간지표.values.tolist())
            cur.executemany(query2, df_분기지표.values.tolist())
            conn.commit()  
        except Exception as e:
            print('save_db() 에러발생')
            print(e)


    print("update_db_companyextr 완료")
    logger.info("update_db_companyextr 완료")


if __name__=='__main__': 

    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # 파일 위치
    
    logger = logging.getLogger('my') # 1.로그 인스턴스를 만든다.    
    formatter = logging.Formatter('[%(levelname)s|%(filename)s:%(lineno)s]%(asctime)s>%(message)s') # 2.formatter를 만든다.
    loggerLevel = logging.DEBUG # 로그레벨 설정
    filename = os.path.join(BASE_DIR, 'update.log') # 로그파일 path설정

    filehandler = logging.FileHandler(filename) # 파일출력
    #streamhandler = logging.StreamHandler() # 콘솔(스트림)출력

    filehandler.setFormatter(formatter) # 각 핸들러에 formatter를 지정한다.
    #streamhandler.setFormatter(formatter)

    # 로그 인스턴스에 스트림 핸들러와 파일 핸들러를 붙인다.
    logger.addHandler(filehandler)
    #logger.addHandler(streamhandler)
    logger.setLevel(loggerLevel)
    logger.info("LOG START") # debug, info, warning, error, critical
        

    model_dict ={'연결연간재무':CompanyStat, '연결분기재무':CompanyStat, 
    '개별연간재무':CompanyStat, '개별분기재무':CompanyStat,
    '연간지표':CompanyExtr, '분기지표':CompanyExtr}

    df_kospi = fdr.StockListing('KOSPI')
    df_kosdaq = fdr.StockListing('KOSDAQ')
    now_time = datetime.today()

    # 재무정보를 업데이트한다.
    # # 종목코드에 해당하는 재무정보 및 재무비율정보를 DB에 업데이트
    update_db_companystat(df_kospi.Symbol.tolist(), start_date='2008', end_date=now_time)
    update_db_companyextr(df_kospi.Symbol.tolist(), start_date='2008', end_date=now_time)
    update_db_companystat(df_kosdaq.Symbol.tolist(), start_date='2008', end_date=now_time)
    update_db_companyextr(df_kosdaq.Symbol.tolist(), start_date='2008', end_date=now_time)

    # df_test = ['005930', '272290', '316140']
    # update_db_companystat(df_test, start_date='2008', end_date=now_time)
    # update_db_companyextr(df_test, start_date='2008', end_date=now_time)

    # df = get_companystat_all(start_date='2015', end_date=now_time) 
    # check_clear_companystat(df) # 데이터 검사(컬럼갯수 등), 실패시 실행중단 
    # update_db_companystat(df) # 장고DB 업데이트

    # 9:00분 ~ 10:05분 , 65분 소요
    # ignore과 replace의 차이점? id 확인
    # db 깨끗히 비우는 방법



            



