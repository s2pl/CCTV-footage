from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class Scraper(models.Model):
    """
    Model to store data scraped from external sources
    """
    username = models.CharField(max_length=255, blank=True, null=True)
    primary_contact = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    additional_emails = models.JSONField(default=dict, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    additional_phones = models.JSONField(default=dict, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    followers = models.IntegerField(blank=True, null=True)
    following = models.IntegerField(blank=True, null=True)
    posts = models.IntegerField(blank=True, null=True)
    social_links = models.JSONField(default=dict, blank=True, null=True)
    contact_methods = models.JSONField(default=dict, blank=True, null=True)
    contact_aggregator = models.JSONField(default=dict, blank=True, null=True)
    
    # Track who created this record
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='scrapers', help_text="User who uploaded this data")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or str(self.id)

    class Meta:
        verbose_name = "Scraper Data"
        verbose_name_plural = "Scraper Data"
