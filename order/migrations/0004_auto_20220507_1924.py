# Generated by Django 3.1.2 on 2022-05-07 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0003_auto_20220507_1914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='car_brand',
            field=models.CharField(default='Марка не указана', max_length=50, verbose_name='Марка автомобиля'),
        ),
    ]
