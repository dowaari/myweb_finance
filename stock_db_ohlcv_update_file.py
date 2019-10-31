import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
import django
django.setup()

import os
import pandas as pd
from pathlib import Path
import sqlite3
import numpy as np
import timeit

class UpdateData:

    def __init__(self, path):
        # 추후 유동적 경로로 수정해야함        
        #self.BASE_PATH = Path(r"./kospi_base_stock_files")
        self.BASE_PATH = path

    def _subdirectories_list(self):
        # BASE_PATH 가 디렉토리라면 디렉토리 내부 모든 파일 경로를 가져오고 리스트에 담아 리턴
        return [x for x in self.BASE_PATH.iterdir() if self.BASE_PATH.is_dir()]

    def read_dataframe(self):
        # 파일 경로의 확장자가 csv라면 pd.read_csv로 해당 파일을 읽음 이 때 index_col은 생성하지 않음.
        df_path_list = self._subdirectories_list()
        for df_path in df_path_list:
            if df_path.suffix == ".csv":
                yield pd.read_csv(df_path, index_col=0, parse_dates=True)



def upadate_kospi_db_fromfile(path):
    conn = sqlite3.connect('./db.sqlite3')
    cur = conn.cursor()

    for idx, df in enumerate(UpdateData(path).read_dataframe()):

        name_code = df.index.name
        df.index.name = "날짜"
        df = df.reset_index(df.index.name)
        name_position = name_code.find('(')
        code = name_code[name_position + 1: -1]
        name = name_code[:name_position]
        df.loc[:, "코드"] = "A" + str(code)
        df["날짜"] = df["날짜"].astype(np.str)
        # df_col = df.columns.tolist()
        df_col = ['날짜', '코드', '시가', '고가', '저가', '종가', '거래량', '시가총액(백만)', '상장주식수(주)']
        # df 순서 바꿈
        df = df[df_col]

        query1 = """
            insert or ignore into nameapp_kospi(date, code, open, high, low, close, volume, total, shares) values(
            ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        try:
            cur.executemany(query1, df[df_col].values.tolist())
            conn.commit()
            print("{}번째, {}, {}완료".format(idx, name, code))
            # if idx > 10:
            #     break
        except Exception as ex:
            print('save_df() 에러발생')
            print(ex)

    cur.close()
    conn.close()
    print("upadate_kospi_db 완료")


def upadate_kosdaq_db_fromfile(path):
    conn = sqlite3.connect('./db.sqlite3')
    cur = conn.cursor()

    for idx, df in enumerate(UpdateData(path).read_dataframe()):

        name_code = df.index.name
        df.index.name = "날짜"
        df = df.reset_index(df.index.name)
        name_position = name_code.find('(')
        code = name_code[name_position + 1: -1]
        name = name_code[:name_position]
        df.loc[:, "코드"] = "A" + str(code)
        df["날짜"] = df["날짜"].astype(np.str)
        # df_col = df.columns.tolist()
        df_col = ['날짜', '코드', '시가', '고가', '저가', '종가', '거래량', '시가총액(백만)', '상장주식수(주)']
        # df 순서 바꿈
        df = df[df_col]

        query1 = """
            insert or ignore into nameapp_kosdaq(date, code, open, high, low, close, volume, total, shares) values(
            ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        try:
            cur.executemany(query1, df[df_col].values.tolist())
            conn.commit()
            print("{}번째, {}, {}완료".format(idx, name, code))
            # if idx > 10:
            #     break
        except Exception as ex:
            print('save_df() 에러발생')
            print(ex)

    cur.close()
    conn.close()
    print("upadate_kosdaq_db 완료")


if __name__=='__main__':   
    
    start = timeit.default_timer()
    
    upadate_kospi_db_fromfile(path=Path(r"./static/kospi_base_stock_files"))  
    upadate_kosdaq_db_fromfile(path=Path(r"./static/kosdaq_base_stock_files"))

    stop = timeit.default_timer()    
    print("Time: ", stop-start)
    # 약 30분 소요