from .base import *

# mysql database Testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'temple-test',
        # 'HOST': 'ls-a7a93a3c9b5410a2f8d0f6ab85930dd16a7da86e.c5kylqbgbcgu.ap-south-1.rds.amazonaws.com',
        'HOST': 'ls-a2caec2a6ab65355700d18af6c9d523c92b46df9.c5kylqbgbcgu.ap-south-1.rds.amazonaws.com',
        'PORT': '3306',
        'USER': 'temple-test',
        'PASSWORD': 'test@2024',
        'CONN_MAX_AGE': 0,
    }
}

# light shell new bucket
AWS_ACCESS_KEY_ID = 'AKIAQG7H242YLLEW2PSJ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_DEFAULT_REGION = 'ap-south-1'
AWS_STORAGE_BUCKET_NAME = 'thozil'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com'
AWS_LOCATION = 'Testing/temple/media'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
