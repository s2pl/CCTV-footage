from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Scraper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(blank=True, max_length=255, null=True)),
                ('primary_contact', models.CharField(blank=True, max_length=255, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('additional_emails', models.JSONField(blank=True, default=dict, null=True)),
                ('phone', models.CharField(blank=True, max_length=255, null=True)),
                ('additional_phones', models.JSONField(blank=True, default=dict, null=True)),
                ('website', models.CharField(blank=True, max_length=255, null=True)),
                ('bio', models.TextField(blank=True, null=True)),
                ('followers', models.IntegerField(blank=True, null=True)),
                ('following', models.IntegerField(blank=True, null=True)),
                ('posts', models.IntegerField(blank=True, null=True)),
                ('social_links', models.JSONField(blank=True, default=dict, null=True)),
                ('contact_methods', models.JSONField(blank=True, default=dict, null=True)),
                ('contact_aggregator', models.JSONField(blank=True, default=dict, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Scraper Data',
                'verbose_name_plural': 'Scraper Data',
            },
        ),
    ] 