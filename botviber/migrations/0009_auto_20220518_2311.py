# Generated by Django 3.1.2 on 2022-05-18 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('botviber', '0008_auto_20220422_1607'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carcreatequestions',
            name='questions',
            field=models.CharField(choices=[('Напишите марку автомобиля', 'Напишите марку автомобиля'), ('Напишите модель автомобиля', 'Напишите модель автомобиля'), ('Напишите номер автомобиля', 'Напишите номер автомобиля'), ('Напишите номер лицензии', 'Напишите номер лицензии'), ('Класс ТС (B, C... )', 'Класс ТС (B, C... )'), ('Сохранить', 'Сохранить')], default='', max_length=100, verbose_name='Сообщения при нажатии на кнопки меню создания автомобиля'),
        ),
        migrations.AlterField(
            model_name='waybillquestions',
            name='questions',
            field=models.CharField(choices=[('Напишите вашу фамилию', 'Напишите вашу фамилию'), ('Напишите ваше имя', 'Напишите ваше имя'), ('Напишите ваше отчество', 'Напишите ваше отчество'), ('Серия водительского удостоверения', 'Серия водительского удостоверения'), ('Номер водительского удостоверения', 'Номер водительского удостоверения'), ('Выбор ТС', 'Выбор ТС'), ('Показание одометра', 'Показание одометра'), ('Для корректной работы сервиса введите ваше текущее время в формате: ЧЧ-ММ', 'Для корректной работы сервиса введите ваше текущее время в формате: ЧЧ-ММ'), ('Ваша заявка отправлена!', 'Ваша заявка отправлена!')], default='', max_length=100, verbose_name='Вопросы'),
        ),
    ]
