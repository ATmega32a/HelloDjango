# Generated by Django 3.1.2 on 2023-10-26 21:04

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0014_auto_20231026_2347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='EDS_valid_from',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='ЭЦП действительна с'),
        ),
        migrations.AlterField(
            model_name='organization',
            name='EDS_valid_to',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='ЭЦП действительна по'),
        ),
    ]
