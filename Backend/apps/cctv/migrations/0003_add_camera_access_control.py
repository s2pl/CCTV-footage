# Generated manually for adding camera access control fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cctv', '0002_recording_codec'),
    ]

    operations = [
        migrations.AddField(
            model_name='camera',
            name='is_public',
            field=models.BooleanField(default=False, help_text='Whether basic users can access this camera'),
        ),
        migrations.AddField(
            model_name='camera',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Whether this camera is active and accessible'),
        ),
    ]
