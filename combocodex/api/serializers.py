from rest_framework.serializers import ModelSerializer
from main.models import Combo

class ComboSerailizer(ModelSerializer):
    class Meta:
        model = Combo
        fields = ['id']