from django.contrib import admin
from .models import Scraper

@admin.register(Scraper)
class ScraperAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'phone', 'website', 'followers', 'following', 'posts']
    search_fields = ['username', 'email', 'phone', 'bio']
    list_filter = ['created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
