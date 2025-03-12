from storages.backends.s3boto3 import S3Boto3Storage

class R2Storage(S3Boto3Storage):
    def url(self, name):
        return f'https://media.combocodex.com/{name}'