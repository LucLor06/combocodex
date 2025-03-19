from rest_framework.serializers import ModelSerializer
from main.models import Combo, Legend, Weapon
from user.models import User

class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['username']


class LegendSerializer(ModelSerializer):
    class Meta:
        model = Legend
        fields = ['name', 'id']


class WeaponSerializer(ModelSerializer):
    class Meta:
        model = Weapon
        fields = ['name', 'id']


class ComboSerailizer(ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    legend_one = LegendSerializer()
    weapon_one = WeaponSerializer()
    legend_two = LegendSerializer()
    weapon_two = WeaponSerializer()
    class Meta:
        model = Combo
        fields = ['id', 'users', 'views', 'video', 'created_on', 'legend_one', 'weapon_one', 'legend_two', 'weapon_two']
