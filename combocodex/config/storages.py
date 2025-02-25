from storages.backends.s3boto3 import S3Boto3Storage
from environment_variables import R2_DEV_ID

class R2DevStorage(S3Boto3Storage):
    def url(self, name):
        return f'https://pub-{R2_DEV_ID}.r2.dev/{name}'