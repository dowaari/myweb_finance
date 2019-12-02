from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from nameapp.models import CompanyStat, CompanyExtr, KospiPredict
from nameapp.serializers import KospiPredictSerializer
from django.shortcuts import redirect

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import mixins
from django.views.generic import View
from django_pandas.io import read_frame

import urllib
from ast import literal_eval
from time import mktime, strptime
from nameapp.backtesting import backtest_run
import pandas as pd

# Create your views here.

def main(request):
    context = {}
    print('main view')  
    return render(request, 'nameapp/home.html', context) 


def addressesbook(request):
    context = {}
    print('addressbook view')
    get_data = request.GET
    code = get_data.get('code', None)
    if CompanyStat.objects.filter(code='A'+code).exists():
        fndata_dy = CompanyStat.objects.filter(code='A'+code, gubun='연결', freq='연간').order_by('-date')
        fndata_dq = CompanyStat.objects.filter(code='A'+code, gubun='연결', freq='분기').order_by('-date')
    else:
        return render(request, 'nameapp/nopersonfound.html', context)
    context['fndata_dy'] = fndata_dy
    context['fndata_dq'] = fndata_dq
    context['code'] = code
    return render(request, 'nameapp/book.html', context)


def get_contacts(request):
    context = {}
    print('get contacts view')
    if request.method == 'GET':
        get_data = request.GET
        data = get_data.get('term','')
        print('get contacts:', data)
        if data == '':
            return render(request, 'nameapp/home.html', context)
        else:
            return redirect('%s?%s' % (reverse('nameapp:addressesbook'),
                                urllib.parse.urlencode({'code': data})))


def notfound(request):
    context = {}
    print('notfound view')    
    return render(request, 'nameapp/nopersonfound.html', context)


def predict_kospi(request):
    context = {}
    context['predict'] = KospiPredict.objects.all().order_by('-date')
    return render(request, 'nameapp/predict_list.html', context)


# 데이터를 JSON 형태로 반환, 결과를 rest framework api view로 보여준다.
# Query Set의 메소드, values, values_list 등 알아보기 
# https://hyunalee.tistory.com/42
# https://lqez.github.io/blog/django-queryset-basic.html
class KospiPredictAPIView(APIView):

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        stocks = KospiPredict.objects.all().order_by('date')

        close_list = []
        real_list = []
        pred_list = []
        signal_list = []
        open_list = []
        label_list = []
        for stock in stocks:
            time_tuple = strptime(str(stock.date), '%Y-%m-%d')  
            utc_now = mktime(time_tuple) * 1000           
            close_list.append([utc_now, stock.close])
            real_list.append([utc_now, stock.real_return])
            pred_list.append([utc_now, stock.pred_return])
            signal_list.append([utc_now, stock.signal])
            open_list.append([utc_now, stock.open])

        buy_records = KospiPredict.objects.filter(buy=1)
        sell_records = KospiPredict.objects.filter(sell=1)
        for buy_record in buy_records:
            time_tuple = strptime(str(buy_record.date), '%Y-%m-%d')  
            utc_now = mktime(time_tuple) * 1000
            label_list.append({'x': utc_now, 'title': 'B', 'text': 'BUY'})
        for sell_record in sell_records:
            time_tuple = strptime(str(sell_record.date), '%Y-%m-%d')  
            utc_now = mktime(time_tuple) * 1000
            label_list.append({'x': utc_now, 'title': 'S', 'text': 'SELL'})              
          
        data = {
            'close': close_list,
            'signal': signal_list,
            'pred': pred_list,
            'open': open_list,
            'label': label_list,
        }

        return Response(data)


class KospiPredictSerializeAPIView(APIView): 

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        stocks = KospiPredict.objects.all().order_by('-date')
        serializer = KospiPredictSerializer(stocks, read_only=True, many=True)
        return Response(serializer.data)


# class KospiPredictListAPI(generics.GenericAPIView, mixins.ListModelMixin):    
#     serializer_class = KospiPredictSerializer
#     def get_queryset(self):
#         return KospiPredict.objects.all().order_by('-date')
#     def get(self, request, *args, **kwargs):
#         return self.list(request, *args, **kwargs)


class ChartView(View):
    def get(self, request, *args, **kwargs):
        backtest_algo1()
        return render(request, 'nameapp/chart.html')


class ChartView1(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'nameapp/chart_copy.html')


def backtest_algo1():

    base_kospi = KospiPredict.objects.all() # DB에 있는 내용으로 백테스팅한다.
    df_result_db = read_frame(base_kospi, fieldnames=['date', 'close', 'open', 'buy', 'sell'])
    #df_result_db['date'] = df_result_db['date'].astype(np.str) # 주의
    df_result_db.set_index('date',inplace=True)
    df_result_db.fillna(0, inplace=True)

    거래결과1, 계좌평가결과1 = backtest_run(df_local=df_result_db, 투자금=10000000, 투자금고정= True, 기간=120)
    수익거래 = 거래결과1[거래결과1['수익률']>0]['수익률']
    손실거래 = 거래결과1[거래결과1['수익률']<0]['수익률']

    # 3개월,6개월,1년 / 거래횟수, win/loss ratio, max win, max loss, sharp ratio, MDD, 수익률sum, mean, std
    print('딥러닝모델전략 성과')
    print('거래횟수:',len(거래결과1), '/', len(계좌평가결과1) )
    print('win:', len(수익거래) )
    print('loss:', len(손실거래) )
    print('win/loss ratio:', len(수익거래) / len(손실거래))
    print('max win:', 수익거래.max() )
    print('max loss:', 손실거래.min() )
    print('수익률합:', round(거래결과1['수익률'].sum(),2), '%')

    과거가격 = 계좌평가결과1.iloc[0]['현재가']
    현재가격 = 계좌평가결과1.iloc[-1]['현재가']
    print('기준수익률:', round(( 현재가격 - 과거가격 ) / 과거가격 * 100 - 0.03,2), '%')


def backtest_algo2():
    # 평균회귀 전략    
    print('평균회귀전략 성과')


    return True

def backtest_algo3():
    # 변동성돌파 전략    
    print('변동성돌파전략 성과')


    return True



