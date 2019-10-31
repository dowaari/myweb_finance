import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_server.settings")
import django
django.setup()

import pandas as pd
from django.db import connections
from django.apps import apps

if __name__ == "__main__":
    
# app과 관련된 db를 초기화, sql_sequence도 초기화
# https://stackoverflow.com/questions/14589634/how-to-reset-the-sequence-for-ids-on-postgresql-tables/14589682#14589682
# https://stackoverflow.com/questions/43663588/executing-djangos-sqlsequencereset-code-from-within-python

    APP_NAME= 'nameapp'
    APPS = apps.get_app_config(APP_NAME)
    for model_name in list(APPS.get_models()):
        print(model_name, 'clear')
        model_name.objects.all().delete()

    conn = connections['default']
    tables = conn.introspection.django_table_names(only_existing=True, include_views=False)
    for table in tables:
        if APP_NAME in table:
            try:                
                sql_query = "UPDATE sqlite_sequence SET seq = '0' WHERE name =\'%s\';" % (table)
                #print(sql_query)
                with conn.cursor() as cur:
                    cur.execute(sql_query)
            except:
                continue
    
