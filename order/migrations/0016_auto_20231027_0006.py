# Generated by Django 3.1.2 on 2023-10-26 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0015_auto_20231027_0004'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='carrier_pdf',
            field=models.FileField(blank=True, default=None, max_length=255, upload_to='permission_taxi', verbose_name='Загрузить разрешение перевозчика'),
        ),
        migrations.AddField(
            model_name='organization',
            name='legal_address',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Юридический адрес'),
        ),
    ]
