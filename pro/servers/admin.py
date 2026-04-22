from django.contrib import admin
from .models import Server

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostname_or_ip', 'status', 'is_active', 'last_heartbeat')
    list_filter = ('status', 'is_active')
    search_fields = ('name', 'hostname_or_ip')
    readonly_fields = ('created_at', 'updated_at', 'last_heartbeat')
