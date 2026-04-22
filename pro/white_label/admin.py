"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from django.contrib import admin
from .models import WhiteLabelConfiguration

@admin.register(WhiteLabelConfiguration)
class WhiteLabelConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
