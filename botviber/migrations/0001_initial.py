# Generated by Django 3.1.2 on 2021-03-26 19:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Button',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('button_id', models.CharField(default='0', max_length=2)),
                ('bg_color', models.CharField(default='#008B8B', max_length=7)),
                ('action_type', models.CharField(default='reply', max_length=5)),
                ('action_body', models.CharField(default='', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Questions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('questions', models.CharField(choices=[('Укажите свой город', 'Укажите свой город'), ('Напишите свою фамилию и имя', 'Напишите свою фамилию и имя'), ('Напишите свой номер телефона', 'Напишите свой номер телефона'), ('Напишите гос. номер вашего автомобиля', 'Напишите гос. номер вашего автомобиля'), ('Напишите марку и модель вашего автомобиля', 'Напишите марку и модель вашего автомобиля'), ('Укажите количество мест', 'Укажите количество мест'), ('Напишите год выпуска автомобиля', 'Напишите год выпуска автомобиля'), ('Напишите тип кузова / грузоподъёмность', 'Напишите тип кузова / грузоподъёмность'), ('Напишите цвет кузова', 'Напишите цвет кузова'), ('Ваша заявка отправлена!', 'Ваша заявка отправлена!')], default='', max_length=100, verbose_name='Вопросы')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionnaireButtons',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('buttons', models.ManyToManyField(related_name='buttons', to='botviber.Button')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer.subscriber')),
            ],
            options={
                'verbose_name': 'Кнопки с вопросами',
                'verbose_name_plural': 'Кнопки с вопросами',
            },
        ),
    ]
