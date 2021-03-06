# Generated by Django 4.0.3 on 2022-03-16 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opensec', '0007_remove_camera_is_onvif_remove_camera_is_ptz'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intruder',
            name='thumbnail',
            field=models.ImageField(blank=True, upload_to='intruder_thumbs', verbose_name='Intruder thumbnail'),
        ),
        migrations.AlterField(
            model_name='intruder',
            name='video',
            field=models.FileField(blank=True, upload_to='intruder_videos', verbose_name='Video of intruder'),
        ),
    ]
