# Generated by Django 3.0.4 on 2020-08-27 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('collab_app', '0005_invite'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='key',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
