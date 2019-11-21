from django.contrib import admin
from nameapp.models import CompanyStat, CompanyExtr, KospiPredict, Kospi, Kosdaq
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
admin.site.register(Kospi)
admin.site.register(Kosdaq)
admin.site.register(KospiPredict)




