from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from nameapp.models import CompanyStat, CompanyExtr
from django.shortcuts import redirect

import urllib
from ast import literal_eval

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