# Generated by Django 4.0.3 on 2022-03-18 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opensec', '0009_alter_intruder_thumbnail_alter_intruder_video'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='camera',
            name='video_framerate',
        ),
        migrations.RemoveField(
            model_name='camera',
            name='video_height',
        ),
        migrations.RemoveField(
            model_name='camera',
            name='video_width',
        ),
    ]
