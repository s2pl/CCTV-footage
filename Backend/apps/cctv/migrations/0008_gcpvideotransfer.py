# Generated migration for GCPVideoTransfer model
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cctv', '0007_recording_storage_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='GCPVideoTransfer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('original_local_path', models.CharField(help_text='Original local file path', max_length=500)),
                ('gcp_storage_path', models.CharField(help_text='Path in GCP bucket', max_length=500)),
                ('gcp_public_url', models.URLField(blank=True, help_text='Public URL to access the video', null=True)),
                ('file_size_bytes', models.BigIntegerField(default=0, help_text='File size in bytes')),
                ('transfer_status', models.CharField(choices=[('pending', 'Pending'), ('uploading', 'Uploading'), ('completed', 'Completed'), ('failed', 'Failed'), ('cleanup_pending', 'Cleanup Pending'), ('cleanup_completed', 'Cleanup Completed')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='When transfer was initiated')),
                ('upload_started_at', models.DateTimeField(blank=True, help_text='When upload started', null=True)),
                ('upload_completed_at', models.DateTimeField(blank=True, help_text='When upload completed', null=True)),
                ('cleanup_scheduled_at', models.DateTimeField(blank=True, help_text='When local file cleanup is scheduled', null=True)),
                ('cleanup_completed_at', models.DateTimeField(blank=True, help_text='When local file was deleted', null=True)),
                ('error_message', models.TextField(blank=True, help_text='Error details if transfer failed', null=True)),
                ('retry_count', models.PositiveIntegerField(default=0, help_text='Number of retry attempts')),
                ('initiated_by', models.ForeignKey(blank=True, help_text='User who initiated this transfer', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='initiated_transfers', to=settings.AUTH_USER_MODEL)),
                ('recording', models.OneToOneField(help_text='Associated recording', on_delete=django.db.models.deletion.CASCADE, related_name='gcp_transfer', to='cctv.recording')),
            ],
            options={
                'verbose_name': 'GCP Video Transfer',
                'verbose_name_plural': 'GCP Video Transfers',
                'ordering': ['-created_at'],
            },
        ),
    ]
