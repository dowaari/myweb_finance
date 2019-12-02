import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
import django
django.setup()
from nameapp.models import KospiPredict
from django.db import IntegrityError
from django_pandas.io import read_frame

import pandas as pd
import numpy as np
import datetime
import FinanceDataReader as fdr
import talib as ta
import scipy.signal
import random
from collections import deque
import logging
import timeit

import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, LSTM, BatchNormalization, LeakyReLU, Flatten, Activation
from keras.optimizers import Nadam
from keras import regularizers

import warnings 
warnings.filterwarnings("ignore")

def add_feature_analysis(df):
    
    df['MA5']= df['종가'].rolling(window= 5).mean()
    df['MA20']= df['종가'].rolling(window= 20).mean()
    df['MADiff']= df['MA5'] - df['MA20']
    df['MA60']= df['종가'].rolling(window= 60).mean()

    # Stochastic_slow_k, Stochastic_slow_d (12,3,3) 모멘텀지표 (상하한)
    df['SlowK'], df['SlowD'] = ta.STOCH(np.array(df['고가'].astype(float)), 
                                        np.array(df['저가'].astype(float)),
                                        np.array(df['종가'].astype(float)),
                                        fastk_period=12, slowk_period=3, slowk_matype=0, 
                                        slowd_period=3, slowd_matype=0)

    # MACD_12_26 , sign, diff 추세지표
    df['MACD'], df['MACDsign'], df['MACDhist'] = ta.MACD(np.array(df['종가'].astype(float)), 
                                                            fastperiod=12, slowperiod=26, signalperiod=9)

    #  RSI_14 모멘텀지표 (상하한)
    df['RSI14']= ta.RSI(np.array(df['종가'].astype(float)), timeperiod=14)     
    #df['전일RSI']= df['RSI'].shift(1)    
        
    # Williams_percent_r_14 모멘텀지표 (상하한)
    df['WILR14'] = ta.WILLR(np.array(df['고가'].astype(float)),
                            np.array(df['저가'].astype(float)),
                            np.array(df['종가'].astype(float)))

    df['DEMA20'] = ta.DEMA(np.array(df['종가'].astype(float)), timeperiod=20)

    df['ADX'] = ta.ADX(np.array(df['고가'].astype(float)),
                    np.array(df['저가'].astype(float)), 
                    np.array(df['종가'].astype(float)), 
                    timeperiod=14)

    df['CCI'] = ta.CCI(np.array(df['고가'].astype(float)),
                    np.array(df['저가'].astype(float)), 
                    np.array(df['종가'].astype(float)), 
                    timeperiod=14)

    df['ATR'] = ta.ATR(np.array(df['고가'].astype(float)),
                    np.array(df['저가'].astype(float)), 
                    np.array(df['종가'].astype(float)), 
                    timeperiod=14)

    df['ROC'] = ta.ROC(np.array(df['종가'].astype(float)), timeperiod=10)

    df['OBV'] = ta.OBV(np.array(df['종가'].astype(float)),
                    np.array(df['거래량'].astype(float)))

    df.dropna(inplace= True) # 결측값 삭제
    df.set_index('날짜', inplace= True) # 날짜를 index로 만든다.

    return df


def log_transform_feature(df, cols):
    for col in cols:   # skew_cols
        df[col] = np.log(df[col] + 1) 
    return df         

def preprocess_feature(df, df_scale):
    features=[] # 제외할 컬럼
    exclude_cols = ['future'] # future_return
    for col in stock_df.columns:
        if col not in exclude_cols: 
            features.append(col)
    for col in features:
        df[col] = (df[col] - df_scale[col][0]) / df_scale[col][1]
    return df

def denoise_feature(df, cols=['future_return']):
    # Savitzky–Golay filter 필터 적용
    for col in cols:
        yhat = scipy.signal.savgol_filter(df[col].values, 15, 3)
        df[col] = pd.Series(yhat, index = df.index)
    return df

# Create Sequences Dataset
# Scaled Dataset
def sequence_generator(panel_df, TIME_SEQ_LEN, suffle=True, seed= 101):
   
    sequential_data = []  # this is a list that will CONTAIN the sequences
    queue = deque(maxlen = TIME_SEQ_LEN)  
  # These will be our actual sequences. 
  # They are made with deque, which keeps the maximum length by popping out older values as new ones come in
    for i in panel_df.values:  # iterate over the values
        queue.append([n for n in i[:-1]])  # store all but the target
        if len(queue) == TIME_SEQ_LEN:  # make sure we have 60 sequences!
            arr_que = np.array(queue)
            #arr_que= (arr_que - arr_que.mean(axis=0)) / arr_que.std(axis=0) # scaling z-score
            sequential_data.append([arr_que, i[-1]])  # append those bad boys!

    if suffle == True:
        random.seed(seed)
        random.shuffle(sequential_data)  # shuffle for good measure.

    X = []
    y = []

    for seq, target in sequential_data:  # going over our new sequential data
        X.append(seq)  # X is the sequences
        y.append(target)  # y is the targets/labels (buys vs sell/notbuy)

    return np.array(X), y  # return X and y...and make X a numpy array!

def classify_trinary(values):    
    gp_std = np.std(values)
    print(gp_std)
    
    target = []
    for value in values:       
        if gp_std < value: 
            target.append(1)
        elif -1*gp_std > value: 
            target.append(-1)         
        else:
            target.append(0)    
    return target


def strategy_run(df_local=None):
    
    SELL_TIME = 3
    SELL_SIG = -1
    BUY_SIG = 1

    ts_list=[]
    time_count= 0
    
    for idate, row in df_local[['prev_signal']].iterrows():

        전일신호 = int(row)
        sell_signal = 0
        buy_signal = 0
        
        #매도 조건: 
        매도조건 = (전일신호 == SELL_SIG) and (time_count > 0) 
        if 매도조건== True:
            sell_signal= 1
            time_count= 0
            
        매도조건 = (time_count > SELL_TIME) 
        if 매도조건== True:
            sell_signal= 1
            time_count= 0  
        
        # 매수 조건
        매수조건 = (전일신호 == BUY_SIG) and (time_count == 0) 
        if 매수조건 == True:
            buy_signal = 1
            time_count = 1
            
        매수조건 = (전일신호 == 1)
        if 매수조건 == True:
            time_count = 1 
        
        ts_list.append([idate, buy_signal, sell_signal])
        
        if time_count > 0:
            time_count += 1 
   
    return pd.DataFrame(data=ts_list, columns=['date','BUY','SELL'])


if __name__ == "__main__":

    # (1) FDR로 자료수집 (1년치)
    # (2) TA-LIB로 기술적지표 추가
    # (3) future_return 목표값 추가 및 Denoising
    # (4) 스케일링: 학습데이터에 사용한 factor(평균과 표준편차)로 스케일링하기
    # (5) 모델불러와서 예측값 출력
    # (6) 예측값 가공, inverse 스케일링
    # (7) 최종값 return df  

    now_time = datetime.date.today() #.strftime('%Y%m%d')
    START_DATE = (now_time - datetime.timedelta(days=400))
    print(now_time, START_DATE)
    
    SCALE_FILE_PATH = './static/kospi_model/scale_dictionary.csv'
    MODEL_FILE_PATH = './static/kospi_model/model_1111_1.hdf5'
    TIME_SEQ_LEN = 20 # how long of a preceeding sequence to collect for RNN
    FUTURE_PERIOD_PREDICT = 3 # how far into the future are we trying to predict?

    df_kospi = fdr.DataReader('KS11', START_DATE)
    df_USD_KRW = fdr.DataReader('USD/KRW', START_DATE)
    df_CNY_KRW = fdr.DataReader('CNY/KRW', START_DATE)
    df_gold = fdr.DataReader('GC', START_DATE)

    df_kospi.reset_index(inplace=True) # 인덱스변경
    df_kospi.columns = ['날짜', '종가', '시가', '고가', '저가', '거래량', '변화율'] # 컬럼명변경
    df_kospi = add_feature_analysis(df_kospi.copy())
    print(df_kospi.shape)

    # 병합
    df_all = pd.merge(df_kospi, df_USD_KRW[['Close']], left_index= True, right_index= True, how='inner')
    df_all = pd.merge(df_all, df_CNY_KRW[['Close']], left_index= True, right_index= True, how='inner')
    df_all = pd.merge(df_all, df_gold[['Close']], left_index= True, right_index= True, how='outer')
    df_all.dropna(subset=['종가'], inplace= True) # 종가 결측값 삭제
    df_all['Close'].fillna(method='ffill', inplace=True) # 금가격 결측값 채우기
    cols_rename = {'Close_x':'USD_KRW','Close_y':'CNY_KRW','Close':'Gold'}
    df_all.rename(columns = cols_rename, inplace=True)
    print(df_all.shape)

    stock_df = df_all.copy()
    stock_df['future'] = stock_df['종가'].shift(-FUTURE_PERIOD_PREDICT)
    stock_df['future'].fillna(method='ffill', inplace= True)
    stock_df['future_return'] = (stock_df['future'] - stock_df['종가']) / stock_df['종가'] * 100
    print(stock_df.shape)
    # 마지막으로 결측값이 없는지 확인이 필요하다.

    scale_dict = pd.read_csv(SCALE_FILE_PATH, encoding='EUC-KR', index_col=0)
    stock_df = log_transform_feature(stock_df.copy(), cols=['거래량', 'ATR', 'ADX'])
    stock_df = preprocess_feature(stock_df.copy(), scale_dict)
    stock_df = denoise_feature(stock_df.copy(), cols=['future_return'])
    print(stock_df.shape)
 
    stock_df.drop(['future', '거래량', '고가', '저가'], axis=1, inplace= True)
    test_X, test_Y = sequence_generator(stock_df.copy(), TIME_SEQ_LEN, suffle=False)
    print(stock_df.shape, test_X.shape)

    # 모델구성부분은 함수로 만들어야한다.
###########################################################
    input_dim = test_X.shape[1:]
    keras.backend.clear_session()
    model = Sequential()

    model.add(LSTM(40, input_shape=input_dim, return_sequences=True, 
                activation='tanh',recurrent_activation='sigmoid',
                activity_regularizer=regularizers.l2(0.01))) #activity_regularizer=regularizers.l2(0.01)
    model.add(BatchNormalization())  
    model.add(Dropout(0.5))

    model.add(LSTM(40, activation='tanh',recurrent_activation='sigmoid',
                activity_regularizer=regularizers.l2(0.01))) # activity_regularizer=regularizers.l2(0.01)
    model.add(BatchNormalization())
    model.add(Dropout(0.5))

    model.add(Dense(10))
    model.add(BatchNormalization())
    model.add(LeakyReLU())
    model.add(Dropout(0.5))

    model.add(Dense(1))
    opt = Nadam(lr=0.005) # 0.005, 0.002, 0.001, 0.01
    model.compile(loss = 'mse', optimizer = opt)

    model.load_weights(MODEL_FILE_PATH)
    predictions = model.predict(test_X)
    score = model.evaluate(test_X, test_Y, verbose=0)
    print('Test loss:', score) # this is mean_squared_error 

###########################################################

    df_result = pd.DataFrame(test_Y, columns= ['real'])
    df_result['pred'] = pd.Series(predictions.reshape(-1))
    yhat = ta.DEMA(np.array(df_result['pred'].astype(float)), timeperiod=3) # 디노이징 이동평균
    df_result['pred_dn'] = pd.Series(yhat, index = df_result.index)
    df_result['pred_change'] = (df_result['pred_dn'] - df_result['pred_dn'].shift(3))
    df_result['classify'] = df_result['pred_change'].transform(classify_trinary)    
    print(df_result.shape)

    df_result_all = pd.merge(stock_df[['종가','시가']].iloc[TIME_SEQ_LEN-1:].reset_index(), df_result, left_index= True, right_index= True)
    df_result_all.rename(columns = {'index':'date','종가':'close','시가':'open'}, inplace=True)
    df_result_all.set_index('date',inplace=True)
    df_result_all['real'].iloc[-3:] = None
    df_result_all['close'] = df_result_all['close'] * scale_dict['종가'][1] + scale_dict['종가'][0]
    df_result_all['open'] = df_result_all['open'] * scale_dict['시가'][1] + scale_dict['시가'][0]
    df_result_all.reset_index(inplace=True)
    df_result_all['date'] = df_result_all['date'].astype(np.str)
    print(df_result_all.shape)
    print(df_result_all.tail())
    # real과 pred의 NaN값은 어떻게 처리?
    # real_return은 denoising 전의 값으로
    # real_return, pred_return 소수점 2째자리까지

######################################################## #DB저장
    for i in range(df_result_all.shape[0]):
        try:
            KospiPredict(
                date = df_result_all.iloc[i,0],
                close = df_result_all.iloc[i,1],
                open = df_result_all.iloc[i,2],
                real_return = df_result_all.iloc[i,3],
                pred_return = df_result_all.iloc[i,6],
                signal = df_result_all.iloc[i,7]).save()
        except IntegrityError: 
            obj = KospiPredict.objects.get(date = df_result_all.iloc[i,0])
            if obj.real_return == None: # 해당값이 없다면 덮어씌우기
                obj.real_return = df_result_all.iloc[i,3]
                obj.save()
            if obj.date == now_time: # 오늘날짜는 덮어씌우기
                obj.close = df_result_all.iloc[i,1]
                obj.open = df_result_all.iloc[i,2]
                obj.pred_return = df_result_all.iloc[i,6]
                obj.signal = df_result_all.iloc[i,7]
                obj.save()
            else: # 그외 중복 ignore
                continue

######################################################## 백테스팅

    #df_result_bt = df_result_all[:].copy()
    base_kospi = KospiPredict.objects.all() # DB에 있는 내용으로 백테스팅한다.
    df_result_bt = read_frame(base_kospi, fieldnames=['date', 'close', 'open', 'signal'])
    df_result_bt['date'] = df_result_bt['date'].astype(np.str) # 주의
    df_result_bt.set_index('date',inplace=True)

    df_result_bt['prev_signal'] = df_result_bt['signal'].shift(1)
    df_result_bt['prev_close'] = df_result_bt['close'].shift(1)
    df_result_bt.fillna(0, inplace=True) # 결측값처리해야한다.

    df_signal= strategy_run(df_result_bt) # 입력 데이터프레임 형식주의, index는 date, prev_signal 컬럼이 있어야함. 
    df_result_all = pd.merge(df_result_all, df_signal, on='date', how='inner')

######################################################## #DB저장
    for i in range(df_result_all.shape[0]):
        try:
            KospiPredict(
                buy = df_result_all.iloc[i,8],
                sell = df_result_all.iloc[i,9]).save()
        except IntegrityError:
            obj = KospiPredict.objects.get(date = df_result_all.iloc[i,0])
            if obj.date == now_time: # 오늘날짜는 덮어씌우기
                obj.buy = df_result_all.iloc[i,8]
                obj.sell = df_result_all.iloc[i,9]
                obj.save()
            else: # 그외 중복 ignore
                continue

    print('코스피예측값 업데이트 완료')



