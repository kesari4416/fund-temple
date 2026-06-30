from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'temple',
        'HOST': '62.72.42.72',
        'PORT': '3306',
        'USER': 'admin',
        'PASSWORD': 'z6za8aq#9?Cx',
        #'CONN_MAX_AGE': 600
    }
}


# light shell new bucket
AWS_ACCESS_KEY_ID = 'AKIAVY2PHBYBVDTP355U'
AWS_SECRET_ACCESS_KEY = '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'
AWS_DEFAULT_REGION = 'ap-south-1'
AWS_STORAGE_BUCKET_NAME = 'ideaux-bucket-prod'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_DEFAULT_REGION}.amazonaws.com'
AWS_LOCATION = 'temple/production/media'

STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

