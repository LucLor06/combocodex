import os
from dotenv import find_dotenv, load_dotenv

path = find_dotenv()

load_dotenv(path)

DJANGO_SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')
R2_DEV_ID = os.getenv('R2_DEV_ID')
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')