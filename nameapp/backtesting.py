
import pandas as pd
import numpy as np
import datetime

# 백테스트 실행, 수정필요: 투자금고정
def backtest_run(df_local=None, 투자금=10000000, 투자금고정=True, 기간=180):

    # 수수료 및 세금 설정
    # 거래 비용: 15.43% (거래 수수료 0.03%, 수익금에 대한 세금: 15.4%)
    거래수수료 = 0.03 # 퍼센테이지
    계산수수료 = (100-거래수수료/2)/100 # 계산수수료
    #세금 = 15.4 # 퍼센테이지

    # 기간설정
    now_date = datetime.date.today() #.strftime('%Y%m%d')
    start_date = (now_date - datetime.timedelta(days=기간))
    print(start_date)
    df_local = df_local.loc[start_date:]

    portfolio = []  # 매수시 [매수일, 매수가, 수량]
    거래결과 = [] # 매도시 [매수가, 매도가, 수익, 수익률]
    계좌평가결과 = [] # [일자, 현재가, 매수가, 매도가, 수량, 매수금액, 평가금액, 투자금, 총자산, BUY, SELL]
    예수금= 투자금

    for idate, row in df_local[['open','close','buy','sell']].iterrows():
        시가, 종가, BUY, SELL = row
        매도가= 0
        매수가2= 0
 
        # 매수 가격: 당일 시가
        # 매도 조건: 당일 종가
        # 슬리피지 없음.

        ############################################################## 매도
        if SELL==1 and len(portfolio) > 0:
            매도가 = 종가
            [매수일,매수가,수량] = portfolio
            수익 = int((매도가 * 수량) * (계산수수료)) - int((매수가 * 수량) * (계산수수료))
            수익률 = round(((매도가 - 매수가) / 매수가 *100 - 거래수수료), 2)  ## 추가
            예수금 = 예수금 + int((매도가 * 수량) * (계산수수료))               
            portfolio = []           
            거래결과.append([idate, 매수가, 매도가, 수익, 수익률])        

        
        ############################################################## 매수
        if BUY == 1 and len(portfolio) == 0:
            매수가 = 시가
            매수가2 = 시가  ## 추가
            
            if (투자금고정 == True) and (투자금 < 예수금): 
                수량 = int(투자금 // (매수가*(계산수수료))) 
                예수금 =  예수금 - int((매수가 * 수량) * (계산수수료))
            else:
                수량 = int(예수금 // (매수가*(계산수수료))) 
                예수금 = 예수금 - int((매수가 * 수량) * (계산수수료))
           
            portfolio = [idate, 매수가, 수량] 
            
             
        # 매일 계좌 평가하여 기록
        ##############################################################
        if len(portfolio) > 0:
            [매수일,매수가,수량] = portfolio
            매수금액 = 매수가 * 수량 # 매수시점 가격기준 평가
            평가금액 = 종가 * 수량 # 금일 종가기준 평가
            총자산 = 평가금액 + 예수금
        else:
            매수가 = 0
            수량 = 0
            매수금액 = 0
            평가금액 = 0
            총자산 = 예수금 
            
        계좌평가결과.append([idate, 종가, 매수가2, 매도가, 수량, 매수금액, 평가금액, 예수금, 총자산, BUY, SELL])
        
    # 거래의 최종 결과
    if (len(df_local) > 0) :
        거래결과 = pd.DataFrame(data=거래결과, columns=['일자','매수가','매도가','수익','수익률'])
        거래결과.set_index('일자', inplace=True)        
        계좌평가결과 = pd.DataFrame(data=계좌평가결과, columns=['일자','현재가','매수가','매도가','수량','매수금액',                                                    
                                                                '평가금액','예수금','총자산','BUY','SELL'])        
        계좌평가결과.set_index('일자', inplace=True)    
        return (거래결과, 계좌평가결과)
    else:
        return (0, 0)


