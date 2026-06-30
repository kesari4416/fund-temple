from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# mysql database developing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'temple',
        'HOST': 'localhost',
        'PORT': '3306',
        'USER': 'appadmin',
        'PASSWORD': 'appadmin',
        'CONN_MAX_AGE': 600
    }
}

# light shell new bucket
AWS_ACCESS_KEY_ID = 'AKIAQG7H242YLLEW2PSJ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_DEFAULT_REGION = 'ap-south-1'
AWS_STORAGE_BUCKET_NAME = 'thozil'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com'
AWS_LOCATION = 'development/temple/media'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
