# Generated by Django 4.0.2 on 2022-03-13 14:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opensec', '0006_remove_camera_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='camera',
            name='is_onvif',
        ),
        migrations.RemoveField(
            model_name='camera',
            name='is_ptz',
        ),
    ]
