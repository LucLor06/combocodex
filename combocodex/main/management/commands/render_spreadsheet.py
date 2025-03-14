from django.core.management.base import BaseCommand
import os
from config.settings import BASE_DIR
from main.models import Legend, Combo
from django.template.loader import render_to_string
from django.urls import reverse
import htmlmin

path = BASE_DIR / 'main/templates/combos'

class Command(BaseCommand):
    help = 'Render spreadsheet'

    def handle(self, *args, **options):
        context = {'legends' : Legend.objects.exclude(name='Universal').prefetch_related('weapons'), 'combos' : Combo.objects.spreadsheet_data(), 'combos_search_url': reverse('combos-search')}
        content = render_to_string(str(path / 'spreadsheet_template.html'), context)
        content = htmlmin.minify(content, remove_empty_space=True, remove_all_empty_space=True)
        with open(str(path / 'rendered_sheet.html'), 'w', encoding='utf-8') as spreadsheet:
            spreadsheet.write(content)
        self.stdout.write(self.style.SUCCESS('Done!'))