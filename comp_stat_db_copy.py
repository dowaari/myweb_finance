
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
## Python이 실행될 때 DJANGO_SETTINGS_MODULE이라는 환경 변수에 현재 프로젝트의 settings.py파일 경로를 등록합니다.
## 이제 장고를 가져와 장고 프로젝트를 사용할 수 있도록 환경을 만듭니다.
import django
django.setup()

import pandas as pd
import sqlite3
from nameapp.models import CompanyStat, CompanyExtr
from django.db import IntegrityError


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


# 기존DB를 장고DB로 복사한다.# 파일실행전 장고DB내용을 모두 삭제, sequence reset 실행
# 팁: 변수이름 한번에 바꾸기 ctrl+f2
def init_db(db_path, table_name, rewrite=False):

    try:
        model_name = model_dict[table_name]
    except:
        print('해당 테이블이 없습니다.')
        return False

    if table_name == '연결연간재무' or table_name == '연결분기재무':
        with sqlite3.connect(db_path) as conn:
            df_local = pd.read_sql("SELECT * From '%s'" %(table_name), con=conn)
        
        printProgressBar(0, df_local.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)        
        for i in range(df_local.shape[0]):
            printProgressBar(i+1, df_local.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)
            try:
                model_name(
                    date = df_local.iloc[i,0], # 행,열
                    code = df_local.iloc[i,12],
                    freq = table_name[2:4],
                    gubun = table_name[0:2],
                    sale = df_local.iloc[i,1], 
                    profit = df_local.iloc[i,2], 
                    netincome = df_local.iloc[i,3],
                    d_netincome = df_local.iloc[i,4], 
                    b_netincome = df_local.iloc[i,5], 
                    asset = df_local.iloc[i,6], 
                    liability = df_local.iloc[i,7],
                    equity = df_local.iloc[i,8], 
                    d_equity = df_local.iloc[i,9], 
                    b_equity = df_local.iloc[i,10],
                    equity_stock = df_local.iloc[i,11]).save()
            
            except IntegrityError:
                obj = model_name.objects.get(
                    date = df_local.iloc[i,0], code = df_local.iloc[i,12],
                    freq = table_name[2:4], gubun = table_name[0:2])
                obj.sale = df_local.iloc[i,1] 
                obj.profit = df_local.iloc[i,2] 
                obj.netincome = df_local.iloc[i,3]
                obj.d_netincome = df_local.iloc[i,4] 
                obj.b_netincome = df_local.iloc[i,5] 
                obj.asset = df_local.iloc[i,6]
                obj.liability = df_local.iloc[i,7]
                obj.equity = df_local.iloc[i,8] 
                obj.d_equity = df_local.iloc[i,9] 
                obj.b_equity = df_local.iloc[i,10]
                obj.equity_stock = df_local.iloc[i,11]
                obj.save()

    elif table_name == '개별연간재무' or table_name == '개별분기재무' :
        with sqlite3.connect(db_path) as conn:
            df_local = pd.read_sql("SELECT * From '%s'" %(table_name), con=conn)

        printProgressBar(0, df_local.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)        
        for i in range(df_local.shape[0]):
            printProgressBar(i+1, df_local.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)
            try:
                model_name(
                    date = df_local.iloc[i,0], # 행,열
                    code = df_local.iloc[i,8],
                    freq = table_name[2:4],
                    gubun = table_name[0:2],
                    sale = df_local.iloc[i,1], 
                    profit = df_local.iloc[i,2], 
                    netincome = df_local.iloc[i,3],
                    d_netincome = df_local.iloc[i,3], # 
                    #b_netincome = df_local.iloc[i,5],
                    asset = df_local.iloc[i,4], 
                    liability = df_local.iloc[i,5],
                    equity = df_local.iloc[i,6], 
                    d_equity = df_local.iloc[i,6], #
                    #b_equity = df_local.iloc[i,10], 
                    equity_stock = df_local.iloc[i,7]).save()
            
            except IntegrityError:
                obj = model_name.objects.get(
                    date = df_local.iloc[i,0], code = df_local.iloc[i,8],
                    freq = table_name[2:4], gubun = table_name[0:2])
                obj.sale = df_local.iloc[i,1] 
                obj.profit = df_local.iloc[i,2] 
                obj.netincome = df_local.iloc[i,3]
                obj.d_netincome = df_local.iloc[i,3] #
                #obj.b_netincome = df_local.iloc[i,5] 
                obj.asset = df_local.iloc[i,4]
                obj.liability = df_local.iloc[i,5]
                obj.equity = df_local.iloc[i,6] 
                obj.d_equity = df_local.iloc[i,6] #
                #obj.b_equity = df_local.iloc[i,10]
                obj.equity_stock = df_local.iloc[i,7]
                obj.save()
 
    elif table_name == '연간지표' or table_name == '분기지표':     
        with sqlite3.connect(db_path) as conn:
            df_local = pd.read_sql("SELECT * From '%s'" %(table_name), con=conn)
        
        printProgressBar(0, df_local.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)  
        for i in range(df_local.shape[0]):        
            printProgressBar(i+1, df_local.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)
            try:
                model_name(
                    date = df_local.iloc[i,0], # 행,열
                    code = df_local.iloc[i,12],
                    freq = table_name[0:2],                                       
                    d_eps = df_local.iloc[i,1], 
                    b_eps = df_local.iloc[i,2], 
                    per = df_local.iloc[i,3],
                    bps = df_local.iloc[i,4], 
                    pbr = df_local.iloc[i,5], 
                    dps = df_local.iloc[i,6], 
                    dps_rate = df_local.iloc[i,7],
                    roe = df_local.iloc[i,8], 
                    netincome_rate = df_local.iloc[i,9], 
                    profit_rate = df_local.iloc[i,10],
                    price = df_local.iloc[i,11]).save()
            
            except IntegrityError:
                obj = model_name.objects.get(
                    date = df_local.iloc[i,0], code = df_local.iloc[i,12],
                    freq = table_name[0:2])
                obj.d_eps = df_local.iloc[i,1] 
                obj.b_eps = df_local.iloc[i,2] 
                obj.per = df_local.iloc[i,3]
                obj.bps = df_local.iloc[i,4] 
                obj.pbr = df_local.iloc[i,5] 
                obj.dps = df_local.iloc[i,6] 
                obj.dps_rate = df_local.iloc[i,7]
                obj.roe = df_local.iloc[i,8] 
                obj.netincome_rate = df_local.iloc[i,9]
                obj.profit_rate = df_local.iloc[i,10]
                obj.price = df_local.iloc[i,11]
                obj.save()

    else:
        print('해당 테이블이 없습니다.')
        return False

    print(table_name, df_local.shape[0], '레코드 복사완료')    

    return True


if __name__=='__main__': 

    model_dict ={'연결연간재무':CompanyStat, '연결분기재무':CompanyStat, 
    '개별연간재무':CompanyStat, '개별분기재무':CompanyStat,
    '연간지표':CompanyExtr, '분기지표':CompanyExtr}
  
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # 파일 위치
    FROM_PATH = os.path.join(BASE_DIR, 'static\company_stat_files\jaemu6.sqlite')
    print(FROM_PATH)

    # 재무정보관련 기존DB를 장고DB로 복사한다.
    init_db(db_path=FROM_PATH, table_name='연결연간재무')
    init_db(db_path=FROM_PATH, table_name='연결분기재무')
    init_db(db_path=FROM_PATH, table_name='개별연간재무')
    init_db(db_path=FROM_PATH, table_name='개별분기재무')
    init_db(db_path=FROM_PATH, table_name='분기지표')
    init_db(db_path=FROM_PATH, table_name='연간지표')

    # 40분 ~ 51분, 11분 소요

    



            



