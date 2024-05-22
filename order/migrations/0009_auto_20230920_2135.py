# Generated by Django 3.1.2 on 2023-09-20 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0008_auto_20230920_2116'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='KPP',
        ),
        migrations.AddField(
            model_name='organization',
            name='OGRN',
            field=models.CharField(default='', max_length=25, verbose_name='ОГРН'),
        ),
    ]
