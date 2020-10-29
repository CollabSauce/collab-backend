# Generated by Django 3.0.4 on 2020-10-29 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collab_app', '0023_auto_20201005_0503'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='has_text_copy_changes',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='task',
            name='text_copy_changes',
            field=models.TextField(blank=True, default=''),
        ),
    ]
