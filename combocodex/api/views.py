from rest_framework.generics import ListAPIView
from main.models import Combo, Legend, Weapon
from .serializers import ComboSerializer, LegendSerializer, WeaponSerializer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from user.models import User
from django.core.exceptions import ValidationError
import time

class ComboListView(ListAPIView):
    serializer_class = ComboSerializer

    def get_queryset(self):
        legends = self.request.query_params.getlist('legends', [])
        weapons = self.request.query_params.getlist('weapons', [])
        print(f'getting combos for {legends} {weapons}')
        combo_data = Combo.objects.search(legends=legends, weapons=weapons, paginate=False)
        print('Done!')
        return combo_data['combos']

    def list(self, request, *args, **kwargs):
        start = time.perf_counter()

        queryset = self.get_queryset()
        combos = list(queryset)

        print(f'Query: {time.perf_counter() - start:.3f}s', flush=True)

        start = time.perf_counter()

        serializer = self.get_serializer(combos, many=True)
        data = serializer.data

        print(f'Serialization: {time.perf_counter() - start:.3f}s', flush=True)

        return Response(data)

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

@api_view(['GET'])
def api_combos_random(request):
    legends = request.query_params.getlist('legends', [])
    weapons = request.query_params.getlist('weapons', [])
    combo = Combo.objects.random(legends=legends, weapons=weapons)
    return Response({'combo': ComboSerializer(combo).data})

@api_view(['POST'])
def api_combos_upload(request):
    post = request.POST
    kwargs = {key.replace('kwarg_', 'is_'): True for key in request.POST if key.startswith('kwarg_')}
    user_ids = [post['user_one_id'], post['user_two_id']]
    usernames = [post['user_one_name'], post['user_two_name']]
    response = {}
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
    try:
        combo = Combo.objects.create_from_post(post, request.FILES, submitter, users=users, **kwargs)
        message = 'Combo successfully submitted'
        status = 200
    except ValidationError as e:
        message = 'There were errors when submitting your combo'
        response['errors'] = '. '.join(e.message_dict.get('__all__', [])) + '.'
        status = 422
    response['message'] = message
    return Response(response, status=status)