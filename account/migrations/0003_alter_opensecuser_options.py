# Generated by Django 4.0.2 on 2022-02-16 14:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_alter_opensecuser_date_added'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='opensecuser',
            options={'verbose_name': 'OpenSec User', 'verbose_name_plural': 'OpenSec Users'},
        ),
    ]