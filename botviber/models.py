from django.db import models

from customer.models import Subscriber
from django.utils.translation import gettext_lazy as _

bg_color = "#008B8B"
text_color = "#ffffff"
non_active_button_color = "#A9A9A9"


class Questions(models.Model):
    class Question(models.TextChoices):
        question_0 = "Укажите свой город", _("Укажите свой город")
        question_1 = "Напишите свою фамилию и имя", _("Напишите свою фамилию и имя")
        question_2 = "Напишите свой номер телефона", _("Напишите свой номер телефона")
        question_3 = "Напишите гос. номер вашего автомобиля", _("Напишите гос. номер вашего автомобиля")
        question_4 = "Напишите марку и модель вашего автомобиля", _("Напишите марку и модель вашего автомобиля")
        question_5 = "Укажите количество мест", _("Укажите количество мест")
        question_6 = "Напишите год выпуска автомобиля", _("Напишите год выпуска автомобиля")
        question_7 = "Напишите тип кузова / грузоподъёмность", _("Напишите тип кузова / грузоподъёмность")
        question_8 = "Напишите цвет кузова", _("Напишите цвет кузова")
        question_9 = "Ваша заявка отправлена!", _("Ваша заявка отправлена!")

    questions = models.CharField(verbose_name="Вопросы", max_length=100,
                                 choices=Question.choices, default="")


class LicensingQuestions(models.Model):
    class LicensingQuestion(models.TextChoices):
        question_0 = "Напишите своё имя", _("Напишите своё имя")
        question_1 = "Напишите свою фамилию", _("Напишите свою фамилию")
        question_2 = "Напишите свой номер телефона", _("Напишите свой номер телефона")
        question_3 = "Напишите гос. номер вашего автомобиля", _("Напишите гос. номер вашего автомобиля")
        question_4 = "Напишите марку вашего автомобиля", _("Напишите марку вашего автомобиля")
        question_5 = "Напишите модель вашего автомобиля", _("Напишите модель вашего автомобиля")
        question_6 = "Отправьте фото первой развёрнутой страницы паспорта", \
                     _("Отправьте фото первой развёрнутой страницы паспорта")
        question_7 = "Отправьте фото паспорта (прописка)", _("Отправьте фото паспорта (прописка)")
        question_8 = "Отправьте фото лицевой стороны СТС", _("Отправьте лицевой задней стороны СТС")
        question_9 = "Отправьте фото задней стороны СТС", _("Отправьте фото задней стороны СТС")
        question_10 = "Ваша заявка отправлена!", _("Ваша заявка отправлена!")

    questions = models.CharField(verbose_name="Вопросы", max_length=100,
                                 choices=LicensingQuestion.choices, default="")


class WaybillQuestions(models.Model):
    class WaybillQuestion(models.TextChoices):
        question_0 = "Напишите вашу фамилию", _("Напишите вашу фамилию")
        question_1 = "Напишите ваше имя", _("Напишите ваше имя")
        question_2 = "Напишите ваше отчество", _("Напишите ваше отчество")
        question_3 = "Серия водительского удостоверения", _("Серия водительского удостоверения")
        question_4 = "Номер водительского удостоверения", _("Номер водительского удостоверения")
        question_5 = "Выбор ТС", _("Выбор ТС")
        question_6 = "Показание одометра", _("Показание одометра")
        question_7 = "Для корректной работы сервиса введите ваше текущее время в формате: ЧЧ-ММ", \
                     _("Для корректной работы сервиса введите ваше текущее время в формате: ЧЧ-ММ")
        question_8 = "Ваша заявка отправлена!", _("Ваша заявка отправлена!")

    questions = models.CharField(verbose_name="Вопросы", max_length=100,
                                 choices=WaybillQuestion.choices, default="")


class CarCreateQuestions(models.Model):
    class CarCreateQuestion(models.TextChoices):
        question_0 = "Напишите марку автомобиля", _("Напишите марку автомобиля")
        question_1 = "Напишите модель автомобиля", _("Напишите модель автомобиля")
        question_2 = "Напишите номер автомобиля", _("Напишите номер автомобиля")
        question_3 = "Напишите номер лицензии", _("Напишите номер лицензии")
        question_4 = "Класс ТС (B, C... )", _("Класс ТС (B, C... )")
        question_5 = "Сохранить", _("Сохранить")

    questions = models.CharField(verbose_name="Сообщения при нажатии на кнопки меню создания автомобиля",
                                 max_length=100,
                                 choices=CarCreateQuestion.choices, default="")


class Button(models.Model):
    button_id = models.CharField(max_length=2, default="0")
    bg_color = models.CharField(max_length=7, default=bg_color)
    action_type = models.CharField(max_length=5, default="reply")
    action_body = models.CharField(max_length=100, default="")


class QuestionnaireButtons(models.Model):
    user = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    buttons = models.ManyToManyField(Button, related_name="buttons")

    def create_buttons(self):
        count = -1
        for q in Questions.Question:
            count += 1
            if q == Questions.Question.question_9:
                button = Button(button_id=count, bg_color=non_active_button_color, action_type="none", action_body=q)
                button.save()
                self.buttons.add(button)

            else:
                button = Button(button_id=count, bg_color=bg_color, action_type="reply", action_body=q)
                button.save()
                self.buttons.add(button)

        self.save()

    def get_buttons(self):
        return ",\n".join(
            [str(i.bg_color) + " " + str(i.action_type) + " " + str(i.action_body) + "\n" for i in self.buttons.all()])

    class Meta:
        verbose_name = "Кнопки с вопросами"
        verbose_name_plural = "Кнопки с вопросами"


class LicensingQuestionnaireButtons(models.Model):
    user = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    buttons = models.ManyToManyField(Button, related_name="licensing_buttons")

    def create_buttons(self):
        count = -1
        for q in LicensingQuestions.LicensingQuestion:
            count += 1
            if q == LicensingQuestions.LicensingQuestion.question_10:
                button = Button(button_id=count, bg_color=non_active_button_color, action_type="none", action_body=q)
                button.save()
                self.buttons.add(button)
            else:
                button = Button(button_id=count, bg_color=bg_color, action_type="reply", action_body=q)
                button.save()
                self.buttons.add(button)
        self.save()

    def get_buttons(self):
        return ",\n".join(
            [str(i.bg_color) + " " + str(i.action_type) + " " + str(i.action_body) + "\n" for i in self.buttons.all()])

    class Meta:
        verbose_name = "Кнопка формы лицензии"
        verbose_name_plural = "Кнопки формы лицензии"


class WaybillQuestionnaireButtons(models.Model):
    edit = models.BooleanField(default=False)
    user = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    buttons = models.ManyToManyField(Button, related_name="waybill_buttons")

    def create_buttons(self):
        count = -1
        for q in WaybillQuestions.WaybillQuestion:
            count += 1
            if q == WaybillQuestions.WaybillQuestion.question_8:

                button = Button(button_id=count, bg_color=non_active_button_color, action_type="none", action_body=q)
                button.save()
                self.buttons.add(button)

            else:
                button = Button(button_id=count, bg_color=bg_color, action_type="reply", action_body=q)
                button.save()
                self.buttons.add(button)
        self.save()

    def get_buttons(self):
        return ",\n".join(
            [str(i.bg_color) + " " + str(i.action_type) + " " + str(i.action_body) + "\n" for i in self.buttons.all()])

    class Meta:
        verbose_name = "Кнопка с вопросом для заказа путёвки"
        verbose_name_plural = "Кнопки с вопросами для заказа путёвки"


class ConditionsForRegions(models.Model):
    region_name = models.CharField("Регион", max_length=32, default="")
    condition = models.CharField("Условие", max_length=1024, default="")

    class Meta:
        verbose_name = "Условие для региона"
        verbose_name_plural = "Условия для регионов"


class CarQuestionnaireButtons(models.Model):
    user = models.ForeignKey(Subscriber, on_delete=models.CASCADE)
    buttons = models.ManyToManyField(Button, related_name="car_buttons")

    def create_buttons(self):
        count = -1
        for q in CarCreateQuestions.CarCreateQuestion:
            count += 1
            if q == CarCreateQuestions.CarCreateQuestion.question_5:
                button = Button(button_id=count, bg_color=non_active_button_color, action_type="none", action_body=q)
                button.save()
                self.buttons.add(button)

            else:
                button = Button(button_id=count, bg_color=bg_color, action_type="reply", action_body=q)
                button.save()
                self.buttons.add(button)

        self.save()

    def get_buttons(self):
        return ",\n".join(
            [str(i.bg_color) + " " + str(i.action_type) + " " + str(i.action_body) + "\n" for i in self.buttons.all()])

    class Meta:
        verbose_name = "Кнопка меню добавления автомобиля"
        verbose_name_plural = "Кнопки меню добавления автомобиля"
