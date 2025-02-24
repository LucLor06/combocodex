from django.apps import AppConfig
from bs4 import BeautifulSoup


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'
    _spreadsheet_soup = None

    def ready(self):
        import main.signals

    @classmethod
    def get_spreadsheet(cls):
        if not cls._spreadsheet_soup:
            cls._spreadsheet_soup = cls.parse_spreadsheet()
        return cls._spreadsheet_soup

    @classmethod
    def parse_spreadsheet(cls):
        from config.settings import BASE_DIR
        with open(str(BASE_DIR / 'main/templates/combos/rendered_sheet.html'), 'r') as sheet:
            html_content = sheet.read()
        return BeautifulSoup(html_content, 'lxml')