from django.contrib import admin
from nameapp.models import CompanyStat, CompanyExtr
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter  # 기간 필터
from admin_numeric_filter.admin import RangeNumericFilter, SliderNumericFilter, NumericFilterModelAdmin # 숫자 범위 필터
# pip install django-admin-rangefilter
# pip install django-admin-numeric-filter


# Register your models here.
class CompanyStatAdmin(admin.ModelAdmin): # admin customizing
    list_display = ['code', 'date', 'freq', 'gubun','sale', 'profit', 'netincome', 'asset',
    'liability', 'equity'] # admin의 레코드 리스트 컬럼지정
    search_fields = ['code'] # 검색박스추가
    list_filter = ['gubun', 'freq'] # 필터 사이드바 추가
    ordering = ('-date',)


class CompanyExtrAdmin(NumericFilterModelAdmin): # admin customizing
    list_display = ['code', 'date', 'freq', 'd_eps', 'b_eps', 'bps', 
    'per', 'pbr', 'roe', 'dps', 'dps_rate', 'profit_rate'] # admin의 레코드 리스트 컬럼지정
    search_fields = ['code'] # 검색박스추가
    list_filter = ('freq', ('per', RangeNumericFilter), ('pbr', RangeNumericFilter),
    ('roe', RangeNumericFilter), ('date', DateRangeFilter),) # 필터 사이드바 추가, range타입사용


admin.site.register(CompanyStat, CompanyStatAdmin)
admin.site.register(CompanyExtr, CompanyExtrAdmin)


    # d_eps =  models.FloatField('연결EPS', null=True)
    # b_eps =  models.FloatField('개별EPS', null=True)
    # per =  models.FloatField('PER', null=True)
    # bps =  models.FloatField('BPS', null=True)
    # pbr =  models.FloatField('PBR', null=True)
    # dps =  models.FloatField('DPS', null=True)
    # dps_rate =  models.FloatField('배당수익률', null=True)
    # roe =  models.FloatField('ROE', null=True)
    # netincome_rate =  models.FloatField('순이익률', null=True)
    # profit_rate =  models.FloatField('영업이익률', null=True)
    # price =  models.FloatField('주가', null=True)
