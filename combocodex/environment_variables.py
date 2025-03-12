import os
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, '.env')

load_dotenv(path)

DJANGO_SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
R2_DEV_ID = os.getenv('R2_DEV_ID')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')