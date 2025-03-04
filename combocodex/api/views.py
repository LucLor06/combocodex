from rest_framework.generics import ListAPIView
from main.models import Combo
from .serializers import ComboSerailizer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.db import IntegrityError
from user.models import User

class ComboListView(ListAPIView):
    serializer_class = ComboSerailizer

    def get_queryset(self):
        legends = self.request.query_params.getlist('legend', [])
        weapons = self.request.query_params.getlist('weapon', [])
        combos, count = Combo.objects.search(legends, weapons, paginate=False)
        return combos