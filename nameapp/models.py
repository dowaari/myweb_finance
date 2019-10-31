from django.db import models

# Create your models here.

# 종목 테이블
class StockTable(models.Model):
    code = models.CharField("종목코드", max_length=10, unique=True, null=False)
    name = models.CharField("종목명", max_length=20, null=False)
    sector = models.CharField("산업구분(KRX)", max_length=100, null=True)
    industry = models.CharField("주요제품(KRX)", max_length=100, null=True)
    #categories = models.CharField("섹터명(NAVER)", max_length=10, null=True)
    division = models.CharField("구분", max_length=10, null=False)

    def __str__(self):
        return '%s %s' % (self.code, self.name) 
        # admin의 record name 표시 변경, (list_display는 좁은 범위 변경)

class Kospi(models.Model):
    date = models.DateField("날짜", max_length=10, null=False)
    code = models.CharField("코드", max_length=10, null=False)
    open = models.FloatField("시가", null=True)
    high = models.FloatField("고가", null=True)
    low = models.FloatField("저가", null=True)
    close = models.FloatField("종가", null=True)
    volume = models.FloatField("거래량", null=True)
    total = models.FloatField("시가총액", null=True)
    shares = models.FloatField("주식수", null=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ('code',)
        unique_together = (('date', 'code'),)  # 쌍으로 unique 설정, 중복불가
        # db_table = 'stock_kospi' # db의 table name을 변경한다.
        verbose_name = '코스피'  # admin의 table name을 변경한다.
        verbose_name_plural = '코스피 기초정보 테이블'


class Kosdaq(models.Model):
    date = models.DateField("날짜", max_length=10, null=False)
    code = models.CharField("코드", max_length=10, null=False)
    open = models.FloatField("시가", null=True)
    high = models.FloatField("고가", null=True)
    low = models.FloatField("저가", null=True)
    close = models.FloatField("종가", null=True)
    volume = models.FloatField("거래량", null=True)
    total = models.FloatField("시가총액", null=True)
    shares = models.FloatField("주식수", null=True)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ('code',)
        unique_together = (('date', 'code'),)  # 쌍으로 unique 설정, 중복불가
        # db_table = 'stock_kodaq' # db의 table name을 변경한다.
        verbose_name = '코스닥'  # admin의 table name을 변경한다.
        verbose_name_plural = '코스닥 기초정보 테이블'


# 재무정보
class CompanyStat(models.Model):
    date = models.CharField('날짜', max_length=10, null=False)
    code = models.CharField('종목코드', max_length=10, null=False)
    freq = models.CharField('주기', max_length=5, null=False)
    gubun = models.CharField('구분', max_length=5, null=False)
    sale =  models.FloatField('매출액', null=True)
    profit =  models.FloatField('영업이익', null=True)
    netincome =  models.FloatField('당기순이익', null=True)
    d_netincome =  models.FloatField('지배순이익', null=True)
    b_netincome =  models.FloatField('비지배순이익', null=True)
    asset =  models.FloatField('자산총계', null=True)
    liability =  models.FloatField('부채총계', null=True)
    equity =  models.FloatField('자본총계', null=True)
    d_equity =  models.FloatField('지배순지분', null=True)
    b_equity =  models.FloatField('비지배지분', null=True)
    equity_stock =  models.FloatField('자본금', null=True)

    class Meta:
        # unique_together를 하면 내부적으로 아래와 같은 구문이 실행된다.
        # CREATE UNIQUE INDEX `nameapp_companyextr_date_code_uniq` ON `nameapp_companyextr` (`date`,`code`);
        unique_together = (('date', 'code', 'freq', 'gubun'),) # 쌍으로 unique 설정, 중복불가
        #db_table = 'Company_D_Year' # db의 table name을 변경한다.
        verbose_name = '재무정보' # admin의 table name을 변경한다.
        verbose_name_plural = '재무정보 테이블'

    # def __str__(self):
    #     return '%s : %s' % (self.code, self.date) # admin의 record name 표시 변경
    
# 재무비율정보
class CompanyExtr(models.Model):
    date = models.CharField('날짜', max_length=10, null=False)
    code = models.CharField('종목코드', max_length=10, null=False)
    freq = models.CharField('주기', max_length=5, null=False)
    d_eps =  models.FloatField('연결EPS', null=True)
    b_eps =  models.FloatField('개별EPS', null=True)
    per =  models.FloatField('PER', null=True)
    bps =  models.FloatField('BPS', null=True)
    pbr =  models.FloatField('PBR', null=True)
    dps =  models.FloatField('DPS', null=True)
    dps_rate =  models.FloatField('배당수익률', null=True)
    roe =  models.FloatField('ROE', null=True)
    netincome_rate =  models.FloatField('순이익률', null=True)
    profit_rate =  models.FloatField('영업이익률', null=True)
    price =  models.FloatField('주가', null=True)

    class Meta:
        unique_together = (('date', 'code', 'freq'),) # 쌍으로 unique 설정, 중복불가
        verbose_name = '재무비율' # admin의 table name을 변경한다.
        verbose_name_plural = '재무비율 테이블'

