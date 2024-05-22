from pathlib import Path

from dateutil.relativedelta import relativedelta

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import Signal, receiver
from django.utils import timezone
from django.utils.html import format_html

from HelloDjango.settings import MEDIA_ROOT
from customer.models import Subscriber

from botviber.utils.api_gibdd import get_info_by_car_number
from botviber.utils.parsing_utilities import parse_car_number

import locale

locale.setlocale(
    category=locale.LC_ALL,
    locale="ru_RU.UTF-8"
)


class Doctor(models.Model):
    surname = models.CharField("Фамилия", max_length=50)
    name = models.CharField("Имя", max_length=50)
    patronymic = models.CharField("Отчество", max_length=50, blank=True)

    EDS_number = models.CharField("Номер сертификата", max_length=64, default='')
    EDS_valid_from = models.DateField("ЭЦП действительна с", default=timezone.now)
    EDS_valid_to = models.DateField("ЭЦП действительна по", default=timezone.now)
    EDS_address = models.CharField("Адрес", max_length=255, default='')

    def __str__(self):
        return str(self.surname) + " " + str(self.name) + " " + str(self.patronymic) + ", " + str(self.EDS_address)

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    def get_doctor_fio(self):
        return f'{self.surname} {self.name[:1]}.{self.patronymic[:1]}.'

    def get_doctor_fullname(self):
        return f'{self.surname} {self.name} {self.patronymic}'


class Mechanic(models.Model):
    surname = models.CharField("Фамилия", max_length=50)
    name = models.CharField("Имя", max_length=50)
    patronymic = models.CharField("Отчество", max_length=50, blank=True)

    EDS_number = models.CharField("Номер удостоверения", max_length=64, default='')
    EDS_valid_from = models.DateField("ЭЦП действительна с", default=timezone.now)
    EDS_valid_to = models.DateField("ЭЦП действительна по", default=timezone.now)
    EDS_address = models.CharField("Адрес", max_length=255, default='')

    def __str__(self):
        return str(self.surname) + " " + str(self.name) + " " + str(self.patronymic) + ", " + str(self.EDS_address)

    class Meta:
        verbose_name = "Механик"
        verbose_name_plural = "Механики"

    def get_mechanic_fio(self):
        return f'{self.surname} {self.name[:1]}.{self.patronymic[:1]}.'

    def get_mechanic_fullname(self):
        return f'{self.surname} {self.name} {self.patronymic}'


class Dispatcher(models.Model):
    surname = models.CharField("Фамилия", max_length=50)
    name = models.CharField("Имя", max_length=50)
    patronymic = models.CharField("Отчество", max_length=50, blank=True)

    EDS_number = models.CharField("Номер удостоверения", max_length=64, default='')
    EDS_valid_from = models.DateField("ЭЦП действительна с", default=timezone.now)
    EDS_valid_to = models.DateField("ЭЦП действительна по", default=timezone.now)
    EDS_address = models.CharField("Адрес", max_length=255, default='')

    def __str__(self):
        return str(self.surname) + " " + str(self.name) + " " + str(self.patronymic) + ", " + str(self.EDS_address)

    class Meta:
        verbose_name = "Диспетчер-нарядчик"
        verbose_name_plural = "Диспетчеры-нарядчики"

    def get_dispatcher_fio(self):
        return f'{self.surname} {self.name[:1]}.{self.patronymic[:1]}.'

    def get_dispatcher_fullname(self):
        return f'{self.surname} {self.name} {self.patronymic}'


class Organization(models.Model):
    LLC = "LLC"
    IndividualEntrepreneur = "IndividualEntrepreneur"

    Form = [
        (LLC, "ООО"),
        (IndividualEntrepreneur, "ИП"),
    ]

    organizational_and_legal_forms = models.CharField(
        "Организационно-правовая форма",
        max_length=25,
        choices=Form,
        default=IndividualEntrepreneur
    )

    name = models.CharField("Название организации", max_length=264, default='')
    legal_address = models.CharField("Юридический адрес", max_length=255, default='', blank=True)
    contract_number = models.CharField("Номер контракта", max_length=20, default='', blank=True)
    EDS_org_name = models.CharField("ЭЦП. Название организации", max_length=128, default='')
    EDS_valid_from = models.DateField("ЭЦП действительна с", default=timezone.now)
    EDS_valid_to = models.DateField("ЭЦП действительна по", default=timezone.now)
    INN = models.CharField("ИНН", unique=True, max_length=25, default='')
    OGRN = models.CharField("ОГРН", unique=True, max_length=25, default='')
    carrier_pdf = models.FileField("Загрузить разрешение перевозчика", upload_to="permission_taxi", max_length=255,
                                   default=None, blank=True)

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, verbose_name='Врач')
    mechanic = models.ForeignKey(Mechanic, on_delete=models.CASCADE, null=True, verbose_name='Механик')
    dispatcher = models.ForeignKey(Dispatcher, on_delete=models.CASCADE, null=True, verbose_name='Диспетчер-нарядчик')

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"

    def __str__(self):
        return self.name


class Order(models.Model):
    order_id = models.CharField("id заказа", max_length=10, default="")
    owner = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Клиент")
    service = models.CharField("Сервис", max_length=100, default="")
    tariff = models.CharField("Тариф", max_length=300, default="")
    from_location = models.CharField("Откуда", max_length=300, default="")
    to_location = models.CharField("Куда", max_length=300, default="")
    order_cost = models.IntegerField("Стоимость заказа, руб. ", default=0)
    comment = models.CharField("Комментарий", max_length=300, default="")
    ord_success = models.BooleanField("Заказ принят водителем", default=False)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class Questionnaire(models.Model):
    applicant = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Соискатель")
    city = models.CharField("Город", max_length=100, default="")
    name = models.CharField("Имя и фамилия", max_length=100, default="")
    phone = models.CharField("Номер телефона", max_length=50, default="")
    car_number = models.CharField("Госномер", max_length=20, default="")
    car_model = models.CharField("Марка и модель", max_length=50, default="")
    number_of_seats = models.CharField("Кол-во посадочных мест", max_length=50, default="")
    car_year_made = models.CharField("Год выпуска", max_length=20, default="")
    car_type = models.CharField("Тип кузова", max_length=50, default="")
    car_color = models.CharField("Тип кузова", max_length=50, default="")

    class Meta:
        verbose_name = "Анкета"
        verbose_name_plural = "Анкеты"


class LicensingQuestionnaire(models.Model):
    applicant = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Водитель")
    name = models.CharField("Имя", max_length=100, default="")
    surname = models.CharField("Фамилия", max_length=100, default="")
    phone = models.CharField("Номер телефона", max_length=50, default="")
    car_number = models.CharField("Госномер", max_length=20, default="")
    car_brand = models.CharField("Марка автомобиля", max_length=50, default="")
    car_model = models.CharField("Модель автомобиля", max_length=50, default="")
    photo_passport_first_path = models.CharField("Первая страница паспорта", max_length=512,
                                                 default=str(Path(MEDIA_ROOT)) + "\\no_photo.png")
    photo_passport_reg_path = models.CharField("Прописка", max_length=512,
                                               default=str(Path(MEDIA_ROOT)) + "\\no_file.jpg")
    photo_sts_front_side_path = models.CharField("СТС передняя сторона", max_length=512,
                                                 default=str(Path(MEDIA_ROOT)) + "\\no_photo.png", )
    photo_sts_back_side_path = models.CharField("СТС задняя сторона", max_length=512,
                                                default=str(Path(MEDIA_ROOT)) + "\\no_photo.png")

    class Meta:
        verbose_name = "Анкета лицензирования"
        verbose_name_plural = "Анкеты лицензирования"


class WaybillEntry(models.Model):
    applicant = models.ForeignKey(Subscriber, on_delete=models.CASCADE, verbose_name="Заявитель")
    organization = models.ForeignKey(Organization, verbose_name="Организация", on_delete=models.CASCADE, null=True)
    phone = models.CharField("Номер телефона", max_length=50, default="")
    number = models.PositiveIntegerField("Номер путевого листа", default=0)
    id_client = models.PositiveIntegerField("Гаражный номер", default=0)
    surname = models.CharField("Фамилия", max_length=50, default="")
    name = models.CharField("Имя", max_length=50, default="")
    patronymic = models.CharField("Отчество", max_length=50, default="")
    ser_doc = models.CharField("Серия удостоверения", max_length=10, default="")
    num_doc = models.CharField("Номер удостоверения", max_length=10, default="")
    num_lic = models.CharField("Номер лицензии", max_length=255, default="")
    kod_org_doc = models.CharField("Класс ТС", max_length=2, default="B")
    tr_reg_num = models.CharField("Гос. номер ТС", max_length=12, default="")
    tr_mark = models.CharField("Марка ТС", max_length=50, default="")
    tr_model = models.CharField("Модель ТС", max_length=50, default="")
    odometer_value = models.CharField("Показание одометра при выезде", max_length=8, default="")
    date = models.CharField("Дата выезда", max_length=10, default="")
    time = models.CharField("Время выезда", max_length=5, default="")
    time_zone = models.CharField("Часовой пояс", max_length=2, default="3")

    closed = models.BooleanField("Путевой лист закрыт?", default=False)
    counter = models.PositiveIntegerField("Счётчик путевых листов", default=0)

    class Meta:
        verbose_name = "Регистрационные данные для путёвки"
        verbose_name_plural = "Регистрационные данные для путёвок"


class WaybillNote(models.Model):
    applicant = models.CharField("Заявитель", max_length=30, default="")
    organization = models.CharField("Название организации", max_length=128, default='')
    phone = models.CharField("Номер телефона", max_length=50, default="")
    number = models.PositiveIntegerField("Номер путевого листа", default=0)
    id_client = models.PositiveIntegerField("Гаражный номер", default=0)
    surname = models.CharField("Фамилия", max_length=50, default="")
    name = models.CharField("Имя", max_length=50, default="")
    patronymic = models.CharField("Отчество", max_length=50, default="")
    ser_doc = models.CharField("Серия удостоверения", max_length=10, default="")
    num_doc = models.CharField("Номер удостоверения", max_length=10, default="")
    num_lic = models.CharField("Номер лицензии", max_length=255, default="")
    kod_org_doc = models.CharField("Класс ТС", max_length=2, default="B")
    tr_reg_num = models.CharField("Гос. номер ТС", max_length=12, default="")
    tr_mark = models.CharField("Марка ТС", max_length=50, default="")
    tr_model = models.CharField("Модель ТС", max_length=50, default="")
    odometer_value = models.CharField("Показание одометра при выезде", max_length=8, default="")
    date = models.CharField("Дата выезда", max_length=10, default="")
    time = models.CharField("Время выезда", max_length=5, default="")
    time_zone = models.CharField("Часовой пояс", max_length=2, default="3")

    arrival_time = models.CharField("Время возвращения", max_length=5, default="", blank=True)
    start_tech_state = models.CharField("Тех.состояние ТС и прицепа в момент выезда", max_length=10,
                                        default="Исправен", blank=True)
    finish_tech_state = models.CharField("Тех.состояние ТС и прицепа по возвращению", max_length=10,
                                         default="", blank=True)
    final_odometer_value = models.CharField("Показание одометра при возвращении", max_length=8,
                                            default="", blank=True)
    fuel_residue = models.CharField("Остаток горючего", max_length=3, default="", blank=True)
    special_marks = models.CharField("Особые отметки", max_length=50, default="", blank=True)
    mechanic_signature = models.CharField("Подпись механика", max_length=25, default="", blank=True)
    driver_signature = models.CharField("Подпись водителя", max_length=25, default="", blank=True)

    def fio_driver(self):
        return str(self.surname) + " " + str(self.name[:1]) + "." + str(self.patronymic[:1]) + "."

    def __str__(self):
        return self.applicant

    def dep_time(self):
        return str(self.time)

    class Meta:
        verbose_name = "Запись в журнале"
        verbose_name_plural = "Записи в журнале"


class WaybillJournal(models.Model):
    journal_counter = models.PositiveIntegerField("Количество путевых листов", default=0)

    class Meta:
        verbose_name = "Регистрация путевого листа"
        verbose_name_plural = "Регистрации путевых листов"


class Car(models.Model):
    organization = models.ForeignKey(Organization, verbose_name="Организация", on_delete=models.CASCADE, null=True,
                                     blank=True)
    car_owner = models.ManyToManyField(Subscriber, verbose_name='Владелец автомобиля', related_name="cars", blank=True)
    car_brand = models.CharField(max_length=50, default='Марка не указана', verbose_name='Марка автомобиля')
    car_model = models.CharField(max_length=50, default='Модель не указана', verbose_name='Модель автомобиля')
    car_number = models.CharField(unique=True, max_length=50, default='Номер не указан',
                                  verbose_name='Гос. номер автомобиля')
    year = models.CharField(max_length=4, default='', verbose_name='Год выпуска', blank=True)
    car_licensing_number = models.CharField(max_length=255, default='Лиц. номер не указан',
                                            verbose_name='Лиценз. номер автомобиля')

    vin_code = models.CharField(max_length=17, verbose_name='VIN', default='', blank=True)
    dc_expiration_date = models.DateField('Дата окончания действия диагностической карты',
                                          default=timezone.now() - relativedelta(days=1))

    vehicle_class = models.CharField("Класс ТС", max_length=2, default="B")
    is_available = models.BooleanField("Доступен", default=True)
    link_for_payment = models.URLField("Ссылка для оплаты", blank=True)
    new_car = Signal(pre_save)

    permission = models.BooleanField("Разрешение такси", default=False)
    permission_pdf = models.FileField("Загрузить документ", upload_to="permission_taxi", max_length=255, default=None, blank=True)
    permission_create_date = models.DateField('Начальная дата разрешения', default=timezone.now)
    permission_cancel_date = models.DateField('Дата аннулирования разрешения',  default=timezone.now, null=True, blank=True)
    
    is_active_license = models.BooleanField("Актуальность лицензии", default=True)   
    color_for_license = models.CharField(max_length=7, default="#FFFFFF")

    permission_related_pairs = models.ManyToManyField('SelfEmployed', verbose_name="Разрешения водителя",
                                                      related_name="cars",
                                                      through='CarFileDocumentPairIntermediate'
                                                      )
    validity_period_of_permit = 5

    def __str__(self):
        return str(self.car_brand) + " " + str(self.car_model) + " " + str(self.car_number)

    def expired_date(self):
        return self.permission_create_date + relativedelta(years=self.validity_period_of_permit)
    
    def get_ti_period(self):
        period = 0
        current_year = datetime.now().year
        if self.year != '':
            car_age = current_year - int(self.year)
            if car_age < 5:
                period = 12
            else:
                period = 6
        return period
    
#    def save(self, *args, **kwargs):
#        if self.vin_code == '':
#            try:
#                car_num = parse_car_number(str(self.car_number))[1]
#                vin, year = get_info_by_car_number(car_num)
#                if vin is not None:
#                    self.vin_code = vin
#                if year != '':
#                    self.year = year
#            except TypeError:
#                pass       
#
#        super(Car, self).save(*args, **kwargs)

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.vin_code == '':
            try:
                car_num = parse_car_number(str(self.car_number))[1]
                vin, year = get_info_by_car_number(car_num)
                if vin is not None:
                    self.vin_code = vin
                if year != '':
                    self.year = year
            except TypeError:
                pass
                
        if self.is_active_license:
            self.color_for_license = '#FFFFFF'
        else:
            self.color_for_license = '#FF0000'

        super(Car, self).save(force_insert, force_update, *args, **kwargs)

    def Дата_аннулирования_разрешения(self):
        if self.permission_cancel_date is not None:
            return format_html(f'<span style="background: {self.color_for_license};">{self.permission_cancel_date.strftime("%d %B %Y")}</span>')

    class Meta:
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"


class SelfEmployed(models.Model):
    user = models.OneToOneField(Subscriber, null=True, on_delete=models.CASCADE, verbose_name="Самозанятый")

    name = models.CharField("Название организации", max_length=264, default='')
    legal_address = models.CharField("Юридический адрес", max_length=255, default='', blank=True)
    contract_number = models.CharField("Номер контракта", max_length=20, default='', blank=True)
    EDS_org_name = models.CharField("ЭЦП. Название организации", max_length=128, default='')
    EDS_valid_from = models.DateField("ЭЦП действительна с", default=timezone.now)
    EDS_valid_to = models.DateField("ЭЦП действительна по", default=timezone.now)
    INN = models.CharField("ИНН", unique=True, max_length=25, default='')
    OGRN = models.CharField("ОГРН", unique=True, max_length=25, default='')

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, null=True, verbose_name='Врач')
    mechanic = models.ForeignKey(Mechanic, on_delete=models.CASCADE, null=True, verbose_name='Механик')
    dispatcher = models.ForeignKey(Dispatcher, on_delete=models.CASCADE, null=True, verbose_name='Диспетчер-нарядчик')

    class Meta:
        verbose_name = "Самозанятый"
        verbose_name_plural = "Самозанятые"

    def __str__(self):
        return self.user.name


class CarFileDocumentPairIntermediate(models.Model):
    self_employed = models.ForeignKey(SelfEmployed, on_delete=models.CASCADE, default='')
    car = models.ForeignKey(Car, verbose_name='Автомобиль', max_length=50, default='', on_delete=models.CASCADE)
    driver_pdf = models.FileField("Загрузить разрешение водителя", upload_to="permission_taxi", max_length=255,
                                  default=None, blank=True)

    class Meta:
        unique_together = (('self_employed', 'car', 'driver_pdf'),)
        verbose_name = "Разрешение водителя"
        verbose_name_plural = "Разрешения водителя"

    def __str__(self):
        return self.driver_pdf.name

    def get_pair(self):
        return self.car, self.driver_pdf.name

    def find_by_car_number(self, car_number):
        for pair in self.objects.all():
            if car_number == pair.car.car_number:
                return self.get_pair()
        return None

    def find_by_driver_pdf(self, driver_pdf):
        for pair in self.objects.all():
            if driver_pdf == pair.driver_pdf:
                return self.get_pair()
        return None


class DCard(models.Model):
    owner = models.ForeignKey(Subscriber, verbose_name="Владелец диагностической карты", on_delete=models.CASCADE)
    car = models.ForeignKey(Car, verbose_name='Автомобиль', max_length=50, default='', on_delete=models.CASCADE)
    vin_code = models.CharField(max_length=17, verbose_name='VIN', default='', blank=True)
    dc_expiration_date = models.DateField('Дата окончания действия диагностической карты',
                                          default=timezone.now() - relativedelta(days=1))
    series_and_number_pts = models.CharField(max_length=10, verbose_name='Серия и номер ПТС', default='', blank=True)
    number_of_failed_attempts = models.PositiveIntegerField("Количество неудачных попыток", default=0)

    is_active = models.BooleanField("Активировать", default=True)
    checking_dc = models.BooleanField("Проверка техосмотра", default=True)

    class Meta:
        verbose_name = "Диагностическая карта"
        verbose_name_plural = "Диагностические карты"

    def __str__(self):
        return str(self.car)
