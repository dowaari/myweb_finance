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

import urllib
from ast import literal_eval
from time import mktime, strptime

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

        # data = {
        #     'date': stocks.values_list('date', flat=True), 
        #     'open': stocks.values_list('open', flat=True),
        #     'close': stocks.values_list('close', flat=True),
        #     'real': stocks.values_list('real_return', flat=True),
        #     'pred': stocks.values_list('pred_return', flat=True),
        #     'signal': stocks.values_list('signal', flat=True),
        # }

        close_list = []
        real_list = []
        pred_list = []
        signal_list = []
        for stock in stocks:
            time_tuple = strptime(str(stock.date), '%Y-%m-%d')  
            utc_now = mktime(time_tuple) * 1000           
            close_list.append([utc_now, stock.close])
            real_list.append([utc_now, stock.real_return])
            pred_list.append([utc_now, stock.pred_return])
            signal_list.append([utc_now, stock.signal])

        data = {
            'close': close_list,
            'signal': signal_list,
            'pred': pred_list,
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
        return render(request, 'nameapp/chart.html')