# Generated by Django 3.0.4 on 2020-08-24 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collab_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='is_resolves',
            field=models.BooleanField(default=False),
        ),
    ]
