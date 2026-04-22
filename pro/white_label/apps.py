"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from django.apps import AppConfig


class WhiteLabelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pro.white_label"
    verbose_name = "White Label"
