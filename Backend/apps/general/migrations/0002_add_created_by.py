# Generated manually for adding created_by field

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_created_by_user_is_admin_user_role'),
        ('general', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scraper',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='scrapers',
                to='users.user',
                help_text='User who uploaded this data'
            ),
        ),
    ]
