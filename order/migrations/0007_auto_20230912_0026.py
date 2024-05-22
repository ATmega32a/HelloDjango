# Generated by Django 3.1.2 on 2023-09-11 21:26

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0006_car_link_for_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='permission_create_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Начальная дата разрешения'),
        ),
        migrations.AddField(
            model_name='car',
            name='permission_pdf',
            field=models.FileField(default=None, max_length=255, upload_to='permission_taxi', verbose_name='Разрешение такси'),
        ),
        migrations.AddField(
            model_name='car',
            name='validity_period_of_permit',
            field=models.PositiveIntegerField(default=0, verbose_name='Срок действия (лет)'),
        ),
    ]
