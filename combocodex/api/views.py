from rest_framework.generics import ListAPIView
from main.models import Combo
from .serializers import ComboSerailizer

class ComboListView(ListAPIView):
    serializer_class = ComboSerailizer

    def get_queryset(self):
        legends = self.request.query_params.getlist('legend', [])
        weapons = self.request.query_params.getlist('weapon', [])
        combos, count = Combo.objects.search(legends, weapons, paginate=False)
        return combos