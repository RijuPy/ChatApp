# Generated by Django 5.1.4 on 2024-12-19 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app2', '0003_userprofileroom_room_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
