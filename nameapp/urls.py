from django.contrib import admin
from django.urls import path, include # 추가
from nameapp import views

app_name= 'nameapp'
urlpatterns = [
    path('', views.main, name='main'),
    path('book/', views.addressesbook, name='addressesbook'),
    path('book-search/', views.get_contacts, name='get_contacts'),
    path('notfound/', views.notfound, name='notfound'),
    path('predict/', views.predict_kospi, name='predict_kospi'),
    path('api/predict/', views.KospiPredictAPIView.as_view(), name="predict_kospi_api"),
    path('api/predict-serialize/', views.KospiPredictSerializeAPIView.as_view()),
    path('chart', views.ChartView.as_view(), name="chart"),
]

# urlpatterns = patterns('',
#     url(r'^docs/', include('rest_framework_swagger.urls')),
#     url(r'^$','addressesapp.views.main'),
#     url(r'^book/','addressesapp.views.addressesbook',name='addressesbook'),
#     url(r'^delete/(?P<name>.*)/','addressesapp.views.delete_person', name='delete_person'),
#     url(r'^book-search/','addressesapp.views.get_contacts', name='get_contacts'),
#     url(r'^addresses-list/', AddressesList.as_view(), name='addresses-list'),
#     url(r'^notfound/','addressesapp.views.notfound',name='notfound'),
#     url(r'^admin/', include(admin.site.urls)),
# )