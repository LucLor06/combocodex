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
        combo_data = Combo.objects.search(legends, weapons, paginate=False)
        return combo_data['combos']


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
    user = authenticate(username=username, password=password)
    if user:
        User.objects.filter(discord_id=discord_id).update(discord_id=None)
        user.discord_id = discord_id
        user.save()
        response = 'Account linked successfully!'
    else:
        response = 'An account with those credentials was not found. Both username and password are case sensitive.'
    return Response({'message': response})

@api_view(['POST'])
def api_combos_upload(request):
    post = request.POST
    kwargs = {key.replace('kwarg_', 'is_'): True for key in request.POST if key.startswith('kwarg_')}
    user_ids = [post['user_one_id'], post['user_two_id']]
    usernames = [post['user_one_name'], post['user_two_name']]
    try:
        submitter = User.objects.get(discord_id=post['discord_id'])
    except User.DoesNotExist:
        submitter = None
    users = []
    for discord_id, username in zip(user_ids, usernames):
        try:
            users.append(User.objects.get(discord_id=discord_id).username)
        except User.DoesNotExist:
            users.append(username)
    combo = Combo.objects.create_from_post(post, request.FILES, submitter, users=users, **kwargs)
    return Response({'message': 'Combo successfully submitted!'})