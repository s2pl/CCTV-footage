from django.db import models
from django.utils.translation import gettext_lazy as _

class AdminPanel(models.Model):
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('pending', _('Pending')),
        ('inactive', _('Inactive')),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_('Name'),
        help_text=_('Enter the name of the item')
    )
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Detailed description of the item'),
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    some_critical_field = models.CharField(
        max_length=255,
        verbose_name=_('Critical Field'),
        help_text=_('This field cannot be modified after creation')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Your Model')
        verbose_name_plural = _('Your Models')
        ordering = ['-created_at']

    def __str__(self):
        return self.name 