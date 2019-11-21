from rest_framework import serializers
from nameapp.models import KospiPredict

class KospiPredictSerializer(serializers.ModelSerializer):

    class Meta:
        model = KospiPredict
        #fields = '__all__' # 필드를 지정할 수 있다.
        exclude = ('id',)
