"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from .models import WhiteLabelConfiguration

def white_label(request):
    """
    Context processor to add the active white label configuration to the template context.
    """
    config = WhiteLabelConfiguration.objects.filter(is_active=True).first()
    return {
        "white_label_config": config
    }
