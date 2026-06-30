from django.contrib import admin
from .models import *

admin.site.register(AssetCategory)
admin.site.register(AssetDetails)
admin.site.register(MoveableAssetCategory)
admin.site.register(MoveableAssetDetails)

