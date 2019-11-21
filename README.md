# myweb_finance
Data Aichemist 웹서비스 구축 프로젝트

- stock_db_clear.py 	          DB 초기화	앱 모델과 관련된 테이블만
- stock_db_table_update.py	    종목테이블 업데이트	매일 실행, 크롤링
- stock_db_ohlcv_update.py	    장기 종목시세 업데이트	최초1회 실행, 크롤링
- stock_db_ohlcv_update_file.py	장기 종목시세 업데이트	최초1회 실행, 백업파일사용
- stock_db_ohlcv_update_day.py	일일 종목시세 업데이트	매일 실행, 크롤링
<br></br>
- comp_stat_db_copy.py	        장기 종목재무 업데이트	최초1회 실행, 백업파일 사용
- comp_stat_db_update.py	      단기 종목시세 업데이트	분기 실행, 크롤링
<br></br>
- stock_kospi_predict.py        KOSPI지수예측값 업데이트 매일 실행
