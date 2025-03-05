from rest_framework.serializers import ModelSerializer
from main.models import Combo, Legend, Weapon

class ComboSerailizer(ModelSerializer):
    class Meta:
        model = Combo
        fields = ['id']


class LegendSerializer(ModelSerializer):
    class Meta:
        model = Legend
        fields = ['name', 'id']


class WeaponSerializer(ModelSerializer):
    class Meta:
        model = Weapon
        fields = ['name', 'id']