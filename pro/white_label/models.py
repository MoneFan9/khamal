"""
PROPRIETARY AND CONFIDENTIAL
This file is part of the Khamal Pro package.
Copyright (c) 2026 Khamal(MoneFan9). All rights reserved.
"""

from django.db import models

class WhiteLabelConfiguration(models.Model):
    """
    Model to store white label configurations like logo and custom CSS.
    """
    name = models.CharField(max_length=255, default="Default Configuration")
    logo = models.ImageField(upload_to="white_label/logos/", null=True, blank=True)
    custom_css = models.TextField(null=True, blank=True, help_text="Custom CSS to be injected into templates.")
    is_active = models.BooleanField(default=False, help_text="Only one configuration can be active at a time.")

    class Meta:
        verbose_name = "White Label Configuration"
        verbose_name_plural = "White Label Configurations"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other configurations
            WhiteLabelConfiguration.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
