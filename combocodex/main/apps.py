from django.apps import AppConfig
from bs4 import BeautifulSoup


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        import main.signals
        from config.settings import BASE_DIR
        with open(str(BASE_DIR / 'main/templates/combos/rendered_sheet.html'), 'r') as sheet:
            html_content = sheet.read()
        global spreadsheet_soup
        spreadsheet_soup = BeautifulSoup(html_content, 'lxml')