from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

class OTP(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['email', 'otp_code']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_valid(self):
        return (
            not self.is_used and 
            timezone.now() <= self.expires_at
        )

    def __str__(self):
        return f"OTP for {self.email}"

class EmailLog(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_message = models.TextField(null=True, blank=True)
    from_email = models.EmailField()
    to_email = models.EmailField()
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Track who created this email
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='email_logs', help_text="User who sent this email")
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    attachments = models.JSONField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['to_email']),
        ]
        ordering = ['-created_at']

    def mark_as_sent(self):
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()

    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.retry_count += 1
        self.save()

    def __str__(self):
        return f"Email to {self.to_email}: {self.subject}"

class CreatorBulkMail(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    campaign_name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    html_message = models.TextField(null=True, blank=True)
    from_email = models.EmailField()
    template_name = models.CharField(max_length=100, default='invitation/invite.html')
    
    # Track who created this campaign
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='creator_bulk_mails', help_text="User who created this campaign")
    
    # Recipients and tracking
    recipient_list = models.JSONField(help_text="List of email addresses")
    template_context = models.JSONField(default=dict, blank=True, help_text="Context variables for the template")
    
    # Status tracking
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    total_recipients = models.IntegerField(default=0)
    successful_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['campaign_name']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Bulk Mail: {self.campaign_name} ({self.status})"
    
    def mark_as_in_progress(self):
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def mark_as_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, error_message):
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save()
    
    def update_counts(self, successful=0, failed=0):
        self.successful_count += successful
        self.failed_count += failed
        self.save()
