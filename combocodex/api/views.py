from rest_framework.generics import ListAPIView
from main.models import Combo, Legend, Weapon
from .serializers import ComboSerailizer, LegendSerializer, WeaponSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from user.models import User

class ComboListView(ListAPIView):
    serializer_class = ComboSerailizer

    def get_queryset(self):
        legends = self.request.query_params.getlist('legend', [])
        weapons = self.request.query_params.getlist('weapon', [])
        combos, count = Combo.objects.search(legends, weapons, paginate=False)
        return combos


class LegendListView(ListAPIView):
    queryset = Legend.objects.all()
    serializer_class = LegendSerializer 
    

class WeaponListView(ListAPIView):
    queryset = Weapon.objects.all()
    serializer_class = WeaponSerializer

@api_view(['POST'])
def api_user_link(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    discord_id = request.POST.get('discord_id')
    print(discord_id)
    print(username)
    print(password)
    user = authenticate(username=username, password=password)
    if user:
        User.objects.filter(discord_id=discord_id).update(discord_id=None)
        user.discord_id = discord_id
        user.save()
        response = 'Account linked successfully!'
    else:
        response = 'An account with those credentials was not found. Both username and password are case sensitive.'
    return Response({'message': response})