# Generated by Django 4.0.2 on 2022-02-17 13:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opensec', '0003_alter_camera_rtsp_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='camera',
            name='rtsp_url',
            field=models.CharField(max_length=200, verbose_name='RTSP URL'),
        ),
    ]
