import concurrent.futures
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Thread

import requests
from dateutil.relativedelta import relativedelta
from viberbot.api.messages import PictureMessage
import order
from botviber.bot_config import viber
from botviber.buttons.buttons import *

from botviber.models import QuestionnaireButtons, ConditionsForRegions, WaybillQuestionnaireButtons, \
    LicensingQuestionnaireButtons, CarQuestionnaireButtons
from botviber.utils.parsing_utilities import parse_car_number, normalize_snils, check_snils
from HelloDjango.exceptions import MissingKeyException, BadRequestException, DCardNotFoundException

from HelloDjango.cancel_order import cancel
from HelloDjango.osm import get_address, coordinates_from_address
from HelloDjango.send_email import send_email
from HelloDjango.send_order import send_order
from HelloDjango.get_distance import distance
from HelloDjango.settings import MEDIA_ROOT, MEDIA_URL, STATIC_URL, STATIC_ROOT
from HelloDjango.waybill import render_pdf_template, pdf_to_png_converter
from customer.models import Subscriber
from order.models import Questionnaire, Order, LicensingQuestionnaire, WaybillEntry, WaybillJournal, WaybillNote, Car, \
    Organization, SelfEmployed, CarFileDocumentPairIntermediate, DCard
from properties import server_url, auth_token, conversation_url
from botviber.utils.api_gibdd import check_dc, check_dc_exp_date, vin_validation, pts_series_number_validation, \
    get_series_number_pts_by_vin

services = {"4": "evacuator", "5": "cargo"}
tariffs = {"4": "Эвакуатор до 2000 кг.", "5": "Эвакуатор до 3000 кг.", "6": "Эвакуатор до 3500 кг.",
           "7": "Эвакуатор до 4000 кг.", "8": "Грузовой 1,5т"}
names_for_files = {"6": "passport_first_page", "7": "passport_registration", "8": "sts_front_side",
                   "9": "sts_back_side"}
local_storage = {}
bg_color = "#008B8B"
text_color = "#FFFFFF"
non_active_button_color = "#A9A9A9"

time_zones = {
    -12: "в формате UTC-12",
    -11: "на Паго-Паго",
    -10: "на Гаваях",
    -9: "на Аляске",
    -8: "в США и Канаде (Тихоокеанское время)",
    -7: "в США и Канаде (Горное время)",
    -6: "в США и Канаде (Центральное время)",
    -5: "в США и Канаде (Восточное время)",
    -4: "в Каракасе",
    -3: "в Сальвадоре",
    -2: "в формате UTC-02",
    -1: "в Кабо-Верде",
    0: "в Лондоне",
    1: "в Париже",
    2: "в Калининграде",
    3: "в Москве",
    4: "в Самаре",
    5: "в Екатеринбурге",
    6: "в Омске",
    7: "в Красноярске",
    8: "в Иркутске",
    9: "в Якутске",
    10: "во Владивостоке",
    11: "в Магадане",
    12: "на Камчатке",
    13: "на островах Феникс",
    14: "на островах Лайн",
}


def is_exists_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not Questionnaire.objects.filter(applicant=s).exists():
        Questionnaire.objects.create(applicant=s)


def is_exists_licensing_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not LicensingQuestionnaire.objects.filter(applicant=s).exists():
        LicensingQuestionnaire.objects.create(applicant=s)


def is_exists_waybill_questionnaire(vid):
    s = Subscriber.objects.get(user=vid)
    if not WaybillEntry.objects.filter(applicant=s).exists():
        WaybillEntry.objects.create(applicant=s, phone=s.phone)


def is_exists_car_number(car_number):
    is_car_number_exists = False
    all_cars = Car.objects.all()
    for car in all_cars:
        if car_number == car.car_number:
            is_car_number_exists = True
    return is_car_number_exists


def set_answer(vid, data, item):
    is_exists_questionnaire(vid)
    s = Subscriber.objects.get(user=vid)
    questionnaire = Questionnaire.objects.get(applicant=s)
    if item == "0":
        questionnaire.city = data
        questionnaire.save()
    elif item == "1":
        questionnaire.name = data
        questionnaire.save()
    elif item == "2":
        questionnaire.phone = data
        questionnaire.save()
    elif item == "3":
        questionnaire.car_number = data
        questionnaire.save()
    elif item == "4":
        questionnaire.car_model = data
        questionnaire.save()
    elif item == "5":
        questionnaire.number_of_seats = data
        questionnaire.save()
    elif item == "6":
        questionnaire.car_year_made = data
        questionnaire.save()
    elif item == "7":
        questionnaire.car_type = data
        questionnaire.save()
    elif item == "8":
        questionnaire.car_color = data
        questionnaire.save()


def set_answer_licensing_question(vid, data, item):
    is_exists_licensing_questionnaire(vid)
    s = Subscriber.objects.get(user=vid)
    licensing_questionnaire = LicensingQuestionnaire.objects.get(applicant=s)
    if item == "0":
        licensing_questionnaire.name = data
        licensing_questionnaire.save()
    elif item == "1":
        licensing_questionnaire.surname = data
        licensing_questionnaire.save()
    elif item == "2":
        licensing_questionnaire.phone = data
        licensing_questionnaire.save()
    elif item == "3":
        licensing_questionnaire.car_number = data
        licensing_questionnaire.save()
    elif item == "4":
        licensing_questionnaire.car_brand = data
        licensing_questionnaire.save()
    elif item == "5":
        licensing_questionnaire.car_model = data
        licensing_questionnaire.save()
    elif item == "6":
        licensing_questionnaire.photo_passport_first_path = str(data)
        licensing_questionnaire.save()
    elif item == "7":
        licensing_questionnaire.photo_passport_reg_path = str(data)
        licensing_questionnaire.save()
    elif item == "8":
        licensing_questionnaire.photo_sts_front_side_path = str(data)
        licensing_questionnaire.save()
    elif item == "9":
        licensing_questionnaire.photo_sts_back_side_path = str(data)
        licensing_questionnaire.save()


def set_answer_waybill_question(vid, data, item, registration=True):
    if data not in ('menu', 'to-menu-from-registered-form'):
        is_exists_waybill_questionnaire(vid)
        subscriber = Subscriber.objects.get(user=vid)
        waybill_questionnaire = WaybillEntry.objects.get(applicant=subscriber)
        if item == "0":
            waybill_questionnaire.surname = data
            waybill_questionnaire.save()
        elif item == "1":
            waybill_questionnaire.name = data
            waybill_questionnaire.save()
        elif item == "2":
            waybill_questionnaire.patronymic = data
            waybill_questionnaire.save()
        elif item == "3":
            waybill_questionnaire.ser_doc = data
            waybill_questionnaire.save()
        elif item == "4":
            waybill_questionnaire.num_doc = data
            waybill_questionnaire.save()
        elif item == "5_0":
            waybill_questionnaire.tr_reg_num = data
            waybill_questionnaire.save()
        elif item == "5_1":
            waybill_questionnaire.tr_mark = data
            waybill_questionnaire.save()
        elif item == "5_2":
            waybill_questionnaire.tr_model = data
            waybill_questionnaire.save()
        elif item == "5_3":
            waybill_questionnaire.num_lic = data
            waybill_questionnaire.save()
        elif item == "5_4":
            waybill_questionnaire.kod_org_doc = data
            waybill_questionnaire.save()
        elif item == "6":
            if registration:
                digits_snils = re.findall(r'\d+', data)
                snils = normalize_snils(''.join(digits_snils))
                if snils == "000-000-000 00":
                    text = "Вы ввели некорректный СНИЛС, внимательно проверьте номер и введите ещё раз"
                    return "retry_6_" + text

                is_correct_snils = check_snils(snils)
                if is_correct_snils:
                    subscriber.SNILS = snils
                    subscriber.save()
                else:
                    text = "Вы ввели некорректный СНИЛС, внимательно проверьте номер и введите ещё раз"
                    return "retry_6_" + text

            else:
                waybill_questionnaire.odometer_value = data
                waybill_questionnaire.save()
        elif item == "7":
            if validate_time_format(data):
                time_zone = set_tz(data)
                waybill_questionnaire.time_zone = time_zone
                waybill_questionnaire.save()
                tz = int(time_zone)
                sign = '+' if tz >= 0 else ''
                try:
                    text = "Ваше время соответствует времени " + time_zones[tz] + ". Ваш часовой пояс - UTC" + sign + \
                           str(waybill_questionnaire.time_zone) + "."
                    viber.send_messages(vid, [TextMessage(text=text, min_api_version=6)])
                except KeyError:
                    text = "Вы, вероятно, ошиблись при вводе времени! Пожалуйста, напишите время в формате Часы-Минуты, " \
                           "например: 12-45"
                    return "retry_7_" + text
            else:
                text = "Ваш ввод не соответствует формату времени, пожалуйста, напишите время в формате Часы-Минуты, " \
                       "например: 12-45"
                return "retry_7_" + text


def set_value_car(vid, data, item):
    local_storage.update({item + vid: data})
    s = Subscriber.objects.get(user=vid)
    waybill_questionnaire = WaybillEntry.objects.get(applicant=s)
    car_num_filter = s.cars.filter(car_number="?")
    car_brand_filter = s.cars.filter(car_brand="?")
    car_model_filter = s.cars.filter(car_model="?")
    car_licensing_number_filter = s.cars.filter(car_licensing_number="?")
    car_vehicle_class = s.cars.filter(vehicle_class="?")
    if not car_num_filter.exists() and not car_brand_filter.exists() and not car_model_filter \
            and not car_licensing_number_filter and not car_vehicle_class:
        s.cars.create(car_brand="?", car_model="?", car_number="?", car_licensing_number='?', vehicle_class='?')
    try:
        car = s.cars.get(car_number="?")
    except order.models.Car.DoesNotExist:
        car = s.cars.get(car_number=local_storage["2" + vid])

    result = True
    if item == "0":
        car.car_brand = data
        car.save()
    elif item == "1":
        car.car_model = data
        car.save()
    elif item == "2":
        if is_exists_car_number(data):
            result = False
        else:
            car.car_number = data
            car.save()
            waybill_questionnaire.tr_reg_num = data
            waybill_questionnaire.save()
    elif item == "3":
        car.car_licensing_number = data
        car.save()
        waybill_questionnaire.num_lic = data
        waybill_questionnaire.save()
    elif item == "4":
        car.vehicle_class = data
        car.save()
        waybill_questionnaire.kod_org_doc = data
        waybill_questionnaire.save()
    return result


def is_exists_order(vid):
    s = Subscriber.objects.get(user=vid)
    if not Order.objects.filter(owner=s).exists():
        Order.objects.create(owner=s)


def get_answer_string(vid):
    s = Subscriber.objects.get(user=vid)
    questionnaire = Questionnaire.objects.get(applicant=s)
    answer_string = "Город: " + questionnaire.city + "\n" + \
                    "Фамилия, имя: " + questionnaire.name + "\n" + \
                    "Телефон: " + questionnaire.phone + "\n" + \
                    "Госномер: " + questionnaire.car_number + "\n" + \
                    "Марка/Модель: " + questionnaire.car_model + "\n" + \
                    "Количество мест: " + questionnaire.number_of_seats + "\n" + \
                    "Год выпуска: " + questionnaire.car_year_made + "\n" + \
                    "Тип кузова/грузоподъёмность: " + questionnaire.car_type + "\n" + \
                    "Цвет: " + questionnaire.car_color + "\n"
    return answer_string


def get_licensing_answer_string(vid):
    s = Subscriber.objects.get(user=vid)
    licensing_questionnaire = LicensingQuestionnaire.objects.get(applicant=s)
    answer_string = "Имя: " + licensing_questionnaire.name + "\n" + \
                    "Фамилия: " + licensing_questionnaire.surname + "\n" + \
                    "Телефон: " + licensing_questionnaire.phone + "\n" + \
                    "Госномер: " + licensing_questionnaire.car_number + "\n" + \
                    "Марка: " + licensing_questionnaire.car_brand + "\n" + \
                    "Модель: " + licensing_questionnaire.car_model + "\n"
    return answer_string


def get_waybill_answer_string(vid, odometer_value=None):
    subscriber = Subscriber.objects.get(user=vid)
    wq = WaybillEntry.objects.get(applicant=subscriber)
    if odometer_value is not None:
        odometer_val = odometer_value
    else:
        odometer_val = wq.odometer_value

    se = SelfEmployed.objects.filter(user=Subscriber.objects.get(user=vid))

    if se.exists():
        organization_mechanic = se.get().mechanic.get_mechanic_fullname()
        organization_doctor = se.get().doctor.get_doctor_fullname()
    else:
        organization_mechanic = wq.organization.mechanic.get_mechanic_fullname()
        organization_doctor = wq.organization.doctor.get_doctor_fullname()

    answer_string = \
        "ФИО: " + wq.surname + " " + wq.name[:1] + "." + wq.patronymic[:1] + ".\n" + \
        "СНИЛС: " + subscriber.SNILS + "\n" + \
        "Номер путёвки: " + str(wq.number) + "\n" + \
        "Гаражный номер: " + str(wq.id_client) + "\n" + \
        "Дата: " + str(wq.date) + "\n" \
                                  "Время: " + str(wq.time) + "\n" \
                                                             "Время отправления: " + str(wq.time) + "\n" \
                                                                                                    "Серия удостоверения: " + str(
            wq.ser_doc) + "\n" + \
        "Номер удостоверения: " + str(wq.num_doc) + "\n" + \
        "Номер лицензии: " + str(wq.num_lic) + "\n" + \
        "Класс ТС: " + str(wq.kod_org_doc) + "\n" + \
        "Госномер: " + str(wq.tr_reg_num) + "\n" + \
        "Марка ТС: " + str(wq.tr_mark) + "\n" + \
        "Модель ТС: " + str(wq.tr_model) + "\n" + \
        "Показание одометра: " + str(odometer_val) + "\n" + \
        "Контроль технического состояния пройден, выпуск на линию разрешён.\n" \
        "Контролёр технического состояния " \
        "автотранспортных средств: " + str(organization_mechanic) + "\n" \
                                                                    "Прошёл предрейсовый медицинский осмотр, к исполнению трудовых обязанностей допущен. " \
                                                                    "Фельдшер: " + str(organization_doctor)
    return answer_string


def get_registration_data_string(vid) -> str:
    subscriber = Subscriber.objects.get(user=vid)
    wq = WaybillEntry.objects.get(applicant=subscriber)

    tz = int(wq.time_zone)
    sign = '+' if tz >= 0 else ''
    return f"Фамилия: {str(wq.surname)}\n" \
           f"Имя: {str(wq.name)}\n" \
           f"Отчество: {str(wq.patronymic)}\n" \
           f"Серия удостоверения: {str(wq.ser_doc)}\n" \
           f"Номер удостоверения: {str(wq.num_doc)}\n" \
           f"Транспортное средство: {str(wq.tr_mark)} {str(wq.tr_model)} {str(wq.tr_reg_num)}\n" \
           f"СНИЛС: {str(subscriber.SNILS)}\n" \
           f"Часовой пояс: UTC{sign}{str(wq.time_zone)}\n"


def get_order_string(vid):
    s = Subscriber.objects.get(user=vid)
    ordering = Order.objects.get(owner=s)
    order_string = "Сервис: " + ordering.service.split("_")[0] + "\n" + \
                   "Тариф: " + tariffs[ordering.tariff] + "\n" + \
                   "Откуда: " + ordering.from_location.split("#")[0] + "\n" + \
                   "Куда: " + ordering.to_location.split("#")[0] + "\n" + \
                   "Комментарий: " + ordering.comment + "\n"
    return order_string


def get_creating_car_string(vid):
    s = Subscriber.objects.get(user=vid)
    car_questionnaire_buttons = CarQuestionnaireButtons.objects.get(user=s)
    creating_car_string = \
        "Марка: " + car_questionnaire_buttons.car_brand + "\n" + \
        "Модель: " + car_questionnaire_buttons.car_model + "\n" + \
        "Номер: " + car_questionnaire_buttons.car_number + "\n"
    return creating_car_string


def conditions(region):
    return ConditionsForRegions.objects.filter(region_name=region).get().condition


def validate_time_format(time):
    pattern = re.compile(r'^([0-1]?[0-9]|2[0-3])\s*[:,.\-_\s]\s*([0-9]|[0-5][0-9])$')
    return True if re.search(pattern, time) else False


def search_by_car(car_attr, query):
    all_cars = Car.objects.all()
    cars_found = set()
    for car in all_cars:
        if str(getattr(car, car_attr)).__contains__(query):
            cars_found.add(car)
    return cars_found


cast = 'https://chatapi.viber.com/pa/broadcast_message'
headers = {'X-Viber-Auth-Token': auth_token}


# def get_btns():
#    return [
#        {'Columns': 6, 'Rows': 1, 'ActionBody': "menu", 'ActionType': "reply",
#         'Silent': 'true', 'Text': "<font color='#ffffff'>{}</font>".format('Принять условия'),
#         'BgColor': bg_color}
#    ]

def get_btns():
    return [
        {'Columns': 6, 'Rows': 2, 'ActionBody': conversation_url, 'ActionType': "open-url", 'OpenURLType': "internal",
         'Silent': 'true', 'Text': "<font size=16 color='#ffffff'>{} {}</font>".format('🌍', 'ОБНОВИТЬ'),
         'BgColor': bg_color}
    ]


def broadcast_text(txt):
    i = -300
    j = -1
    number = Subscriber.objects.count()
    customers = Subscriber.objects.all()
    while j < number:
        i += 300
        j += 300
        recipient = list(customers[i:j].values_list('user', flat=True))
        bcast = dict(broadcast_list=recipient)
        mess = dict(bcast, min_api_version=6, type="text", sender=dict(name="МарусЪя Транспортные Услуги"),
                    tracking_data="tow",
                    text=txt, keyboard=dict(Type="keyboard", InputFieldState="hidden", Buttons=get_btns()))
        requests.post(cast, json.dumps(mess), headers=headers)


def message_handler(viber_request):
    vid = viber_request.sender.id
    name = viber_request.sender.name
    action_body = str(viber_request.message.text)
    tracking_data = str(viber_request.message.tracking_data)
    subscriber = Subscriber.objects.get(user=vid)
    is_exists_order(vid)
    ordering = Order.objects.get(owner=subscriber)
    wbe_for_subscriber = WaybillEntry.objects.filter(applicant=subscriber)

    if vid == 'PXiguHPVx8vHp6O/asKvcg==' and action_body[:4] == 'Всем':
        broadcast_text(action_body[4:])
        return False

    if tracking_data.startswith("job-app-form"):
        form_thread(vid, action_body, tracking_data, job_app_form_handler)
    elif tracking_data.startswith("license-app-form"):
        form_thread(vid, action_body, tracking_data, license_app_form_handler)
    elif tracking_data.startswith("waybill-app-form") or tracking_data.startswith('kb-waybill-app-form'):
        form_thread(vid, action_body, tracking_data, waybill_form_handler)
    elif tracking_data == "from" and not action_body.startswith("/back"):
        from_loc = action_body + "#" + coordinates_from_address(action_body)
        ordering.from_location = from_loc
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место отправления:\n" + action_body), to_address()])
    elif tracking_data == "to" and not action_body.startswith("/back"):
        to_loc = action_body + "#" + coordinates_from_address(action_body)
        ordering.to_location = to_loc
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место прибытия:\n" + action_body), comment()])
    elif tracking_data == 'enter-radius-distance':
        radius_distance = action_body
        viber.send_messages(vid, [driver_location_kb(radius_distance)])
    elif tracking_data == 'support_letter':
        if action_body not in ("menu", "info"):
            sender = str(name) + " " + str(subscriber.phone)
            send_email("Письмо в техподдержку от " + sender, action_body)
            viber.send_messages(vid, [TextMessage(text="Ваше сообщение отправлено в техподдержку", min_api_version=6),
                                      info()])
    elif tracking_data == "set-snils":
        if not action_body == "menu":

            digits_snils = re.findall(r'\d+', action_body)
            snils = normalize_snils(''.join(digits_snils))
            if snils == "000-000-000 00":
                text = "Вы ввели некорректный СНИЛС, внимательно проверьте номер и введите ещё раз"
                return "retry_6_" + text
            is_correct_snils = check_snils(snils)
            if is_correct_snils:
                subscriber.SNILS = snils
                subscriber.save()
                text = "Проверьте правильность заполнения\n\n" + str(get_registration_data_string(vid))
                viber.send_messages(vid, TextMessage(text=text, keyboard=confirm_or_correct_kb(), min_api_version=6))
            else:
                text = "Вы ввели некорректный СНИЛС, внимательно проверьте номер и введите ещё раз"
                viber.send_messages(vid,
                                    TextMessage(text=text, tracking_data="set-snils",
                                                min_api_version=6, keyboard=enter_later_kb()))

    if action_body == "start":
        viber.send_messages(vid, [refresh_menu_rich(), choice_service(viber_request.sender.id)])

    elif action_body == "menu":
        viber.send_messages(vid, [KeyboardMessage(keyboard=main_menu_kb(vid),
                                                  min_api_version=6)])

    elif action_body == "back-to-menu":
        car = Car.objects.filter(car_owner=Subscriber.objects.get(user=vid)).last()
        car.delete()
        viber.send_messages(vid, messages=[refresh_menu_rich(), choice_service(viber_request.sender.id)])

    elif action_body == "cargo":
        ordering.service = "Грузоперевозки_5"
        ordering.save()
        viber.send_messages(vid, [choice_cargo_tariff()])

    elif action_body == "evacuator":
        ordering.service = "Эвакуатор_4"
        ordering.save()
        viber.send_messages(vid, [choice_evacuator_tariff()])

    elif action_body == "app_job":
        viber.send_messages(vid,
                            [job_application_form(vid=vid, number_button=None, text="Заявка на работу",
                                                  text_field="hidden")])

    elif action_body.startswith("job"):
        number_button = action_body.split('_')[1]
        text = action_body.split('_')[2]
        viber.send_messages(vid,
                            [job_application_form(vid=vid, number_button=number_button, text=text,
                                                  order_data=number_button, text_field="regular")])

    elif action_body == "send_application":
        send_email("Заявка на работу от " + str(Questionnaire.objects.get(applicant=subscriber).name),
                   get_answer_string(vid))
        viber.send_messages(vid, [TextMessage(text="Ваша заявка отправлена\n" + get_answer_string(vid)),
                                  return_to_menu_rich()])

    elif action_body == "send_licensing_application":
        lq = LicensingQuestionnaire.objects.get(applicant=subscriber)
        try:
            files_to_attach = [
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_passport_first_path).split("media/")[1])),
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_passport_reg_path).split("media/")[1])),
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_sts_front_side_path).split("media/")[1])),
                Path(MEDIA_ROOT).joinpath(Path(str(lq.photo_sts_back_side_path).split("media/")[1]))
            ]
        except IndexError:
            t = Thread(target=send_email, args=["Запрос на лицензирование, " + str(lq.name),
                                                get_licensing_answer_string(vid)])
            t.setDaemon(True)
            t.start()

            viber.send_messages(vid, [TextMessage(text="Ваша заявка отправлена\n" + get_licensing_answer_string(vid)),
                                      return_to_menu_rich()])
            return

        t = Thread(target=send_email, args=["Запрос на лицензирование, " + str(lq.name),
                                            get_licensing_answer_string(vid), None, None, None, files_to_attach])
        t.setDaemon(True)
        t.start()
        viber.send_messages(vid, [TextMessage(text="Ваша заявка отправлена\n" + get_licensing_answer_string(vid)),
                                  return_to_menu_rich()])

    elif action_body == "waybill":
        if not wbe_for_subscriber.exists():
            set_edit_waybill_buttons(vid, False)
            viber.send_messages(vid,
                                [waybill_form(vid=vid, number_button=None, text="Заявка на путевой лист",
                                              text_field="hidden")])
        else:
            if subscriber.is_admin or admissibility_of_receiving_waybill(vid):
                url, path_to_pdf, file_name_pdf, user_path = waybill_build(vid)
                viber.send_messages(vid, [download_waybill_or_edit_kb()])

    elif action_body == "to-menu-from-registered-form":
        if not verify_registration_data(vid)[0]:
            text = "Проверьте правильность заполнения\n\n" + str(get_registration_data_string(vid))
            text_non_verify = ''
            if not verify_registration_data(vid)[0]:
                empty_fields = ', '.join(verify_registration_data(vid)[1])
                text_non_verify = f"\nВы не сможете получить путёвку, т.к. у вас не заполнены следующие поля : {empty_fields}"

            text = text + text_non_verify
            viber.send_messages(vid, [TextMessage(text=text, min_api_version=6),
                                      return_to_entering_data(vid)])  # todo "Тут ещё добавить кнопку rich
            # типа Ввести данные или как-то так или Перейти к заполнению данных"
        viber.send_messages(vid, [KeyboardMessage(keyboard=main_menu_kb(vid),
                                                  min_api_version=6)])

    elif action_body == "user-registration":
        set_edit_waybill_buttons(vid, True)
        viber.send_messages(vid,
                            [waybill_form(vid=vid, number_button=None,
                                          text="Для изменения данных нажмите соответствующую кнопку, введите значение "
                                               "и нажмите отправить",
                                          text_field="hidden")])
    elif action_body == "set-snils":
        viber.send_messages(vid, TextMessage(text="Введите номер СНИЛС", tracking_data="set-snils", min_api_version=6))

    elif action_body == "verify-data":
        text = "Проверьте правильность заполнения\n\n" + str(get_registration_data_string(vid))
        text_non_verify = ''
        if not verify_registration_data(vid)[0]:
            empty_fields = ', '.join(verify_registration_data(vid)[1])
            text_non_verify = f"\nВы не сможете получить путёвку, т.к. у вас не заполнены следующие поля : {empty_fields}"

        text = text + text_non_verify
        viber.send_messages(vid, TextMessage(text=text, keyboard=confirm_or_correct_kb(), min_api_version=6))

    elif action_body == "set-odometer":
        if not subscriber.is_driver:
            # return viber.send_messages(vid,
            #                            TextMessage(
            #                                text="Администратор временно ограничил вас в получении путевого листа,"
            #                                     " ваш СНИЛС не прошёл проверку подлинности, проверьте правильность "
            #                                     "ввода и введите его повторно в личном кабинете",
            #                                keyboard=main_menu_kb(vid),
            #                                min_api_version=6))
            return viber.send_messages(vid,
                                       TextMessage(
                                           text="Вы заблокированы, для разблокировки свяжитесь с администратором",
                                           keyboard=main_menu_kb(vid),
                                           min_api_version=6))
        if not verify_registration_data(vid)[0]:
            text = "Проверьте правильность заполнения\n\n" + str(get_registration_data_string(vid))
            text_non_verify = ''
            if not verify_registration_data(vid)[0]:
                empty_fields = ', '.join(verify_registration_data(vid)[1])
                text_non_verify = f"\nВы не сможете получить путёвку, т.к. у вас не заполнены следующие поля : {empty_fields}"

            text = text + text_non_verify
            return viber.send_messages(vid, [TextMessage(text=text, min_api_version=6),
                                             return_to_entering_data(vid)])  # todo "Тут ещё добавить кнопку rich
            # типа Ввести данные или как-то так или Перейти к заполнению данных"
        viber.send_messages(vid, [KeyboardMessage(keyboard=main_menu_kb(vid),
                                                  min_api_version=6)])
        car_filter = Car.objects.filter(car_owner=subscriber)
        if car_filter.exists():
            if car_filter.count() == 1:
                car = car_filter.get()
                d_card = get_d_card(subscriber, car)
                if d_card.checking_dc:
                    if d_card.vin_code != '':
                        if not check_dc_exp_date(d_card.dc_expiration_date) or not d_card.is_active:
                            if d_card.number_of_failed_attempts > 0:
                                if d_card.number_of_failed_attempts > 2:
                                    text_1 = f"Вам отказано в получении путевого листа для автомобиля " \
                                             f"{car.car_number}, т.к. у вас не пройден техосмотр.\n\n" \
                                             "1) Вам необходимо пройти полугодовой технический осмотр\n" \
                                             "2) Сообщить администратору о наличии актуальной " \
                                             "диагностической карты\n" \
                                             "3) После того как администратор сообщит Вам что " \
                                             "разрешается подтвердить наличие диагностической карты - " \
                                             "нажмите на кнопку \"Подтвердить техосмотр\"\n"
                                    return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text_1, car))

                                text_2 = f"Вам отказано в получении путевого листа, т.к. диагностическая карта " \
                                         f"автомобиля {car} просрочена\n\n" \
                                         f"1) Вам необходимо пройти полугодовой технический осмотр\n" \
                                         f"2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
                                return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text_2, car))
                    d_card.number_of_failed_attempts = 0
                    d_card.save()

        if not wbe_for_subscriber.exists():
            set_edit_waybill_buttons(vid, False)
            viber.send_messages(vid, [waybill_form(vid=vid, number_button=None, text="Заявка на путевой лист",
                                                   text_field="hidden")])
        else:
            if subscriber.is_admin or admissibility_of_receiving_waybill(vid):
                if subscriber.SNILS == '':
                    viber.send_messages(vid, [notify_for_entering_data_rich(),
                                              TextMessage(text="Введите показание одометра", min_api_version=6,
                                                          tracking_data="set-car"), cancel_kb("set-car")])
                else:
                    viber.send_messages(vid, [TextMessage(text="Введите показание одометра", min_api_version=6,
                                                          tracking_data="set-car"), cancel_kb("set-car")])

    elif tracking_data == "set-car":
        set_answer_waybill_question(vid, action_body, '6', False)
        viber.send_messages(vid, choice_from_my_cars(vid, next_to='to-quick-create-waybill'))
    elif tracking_data.startswith("save-odometer-value"):
        odometer_value = action_body.split('_')[0]
        car_number = action_body.split('_')[1]
        car = subscriber.cars.get(car_number=car_number)
        car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
        if not car.is_available:
            return viber.send_messages(vid, to_menu_kb("Автомобиль " + car_str +
                                                       " заблокирован, вам отказано в получении "
                                                       "путевого листа!"))
        if not car.is_active_license:
            return viber.send_messages(vid, to_menu_kb("Автомобиль " + car_str +
                                       " заблокирован, вам отказано в получении путевого листа!"))
        viber.send_messages(vid, quick_create_waybill(vid, car, odometer_value))
    
    elif action_body.startswith('pts-info'):
        tracking_data = action_body.split("pts-info_")[1]
        url_pic = server_url + MEDIA_URL + 'sts.jpg'
        return viber.send_messages(vid, [
            TextMessage(text="Серию и номер паспорта ТС можно посмотреть как в самом ПТС или "
                             "его электронном аналоге - ЭПТС, "
                             "так и в СТС, в пункте \"Паспорт ТС\"", tracking_data=tracking_data),
            PictureMessage(media=url_pic, min_api_version=6, tracking_data=tracking_data,
                           keyboard=to_main_kb())])

    elif tracking_data.startswith('pts-series-number'):
        data = tracking_data.split("_")
        car_number = data[1]
        vin = data[2]
        odometer_value = wbe_for_subscriber.get().odometer_value
        car = Car.objects.get(car_number=car_number)
        
        _pts_ser_num = action_body
        pts_ser_num = pts_series_number_validation(_pts_ser_num)[0]
        text_error = pts_series_number_validation(_pts_ser_num)[1]
        d_card = get_d_card(subscriber, car)
        
        if text_error != '':
            tracking_data = f'pts-series-number_{car_number}_{odometer_value}'
            viber.send_messages(vid,
                                [TextMessage(text=text_error, tracking_data=tracking_data), cancel_kb(tracking_data)])
        else:
            text = "Ваши серия и номер ПТС проверяются, пожалуйста, ожидайте ответа."
            viber.send_messages(vid, TextMessage(text=text, keyboard=main_menu_kb(vin), min_api_version=6))
            with concurrent.futures.ThreadPoolExecutor() as executor:
                pts_ser_num_from_request = executor.submit(get_series_number_pts_by_vin, vin)
                pts_ser_num_result = pts_ser_num_from_request.result(timeout=30)
                if pts_ser_num == pts_ser_num_result:
                    d_card.series_and_number_pts = pts_ser_num
                    d_card.save()
                    future = executor.submit(waybill_build, vid, odometer_value, car)
                    url, path_to_pdf, file_name_pdf, user_path = future.result()
                    executor.submit(create_note, vid)
                    executor.submit(pdf_to_png_converter, str(path_to_pdf))

                    url_to_image_waybill = url[:-4] + ".png"
                    return viber.send_messages(vid, [TextMessage(text="Путевой лист легкового автомобиля\n" + get_waybill_answer_string(vid)),
                            PictureMessage(media=url_to_image_waybill, min_api_version=6),
                            to_menu_and_permission_taxi_kb(vid)])
                else:
                    text = f"Вам отказано в получении путевого листа, т.к. ПТС с серией и номером {pts_ser_num} " \
                           f"не принадлежит автомобилю {car}"
                    return viber.send_messages(vid,
                                               TextMessage(text=text, keyboard=main_menu_kb(vin), min_api_version=6))

    elif tracking_data.startswith('vin-code'):
        data = tracking_data.split("_")
        car_number = data[1]
        odometer_value = wbe_for_subscriber.get().odometer_value
        car = Car.objects.get(car_number=car_number)
        _vin = action_body
        vin = vin_validation(_vin)[0]
        if car.vin_code != vin:
            d_card = get_d_card(subscriber, car)
            d_card.delete()
            car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
            return viber.send_messages(vid, to_menu_kb("Вы ввели неправильный VIN автомобиля " + car_str + ", вам отказано в получении путевого листа!"))
        text_error = vin_validation(_vin)[1]
        d_card = get_d_card(subscriber, car)
        
        if text_error != '':
            tracking_data = f'vin-code_{car_number}_{odometer_value}'
            viber.send_messages(vid,
                                [TextMessage(text=text_error, tracking_data=tracking_data), cancel_kb(tracking_data)])
        else:
            d_card.vin_code = vin
            d_card.save()
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(check_dc, vin)

                    dc_expiration_date = datetime.strptime(future.result(), '%Y-%m-%d').date()
                    d_card.dc_expiration_date = dc_expiration_date
                    d_card.save()

                    if not check_dc_exp_date(dc_expiration_date) or not d_card.is_active:
                        d_card.number_of_failed_attempts += 1
                        if (d_card.number_of_failed_attempts + 1) > 2:
                            d_card.is_active = False
                        d_card.save()
                        text = f"Вам отказано в получении путевого листа, т.к. " \
                               f"отсутствует диагностическая карта автомобиля {car}\n\n" \
                               "1) Вам необходимо пройти полугодовой технический осмотр\n" \
                               "2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
                        return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))
                    else:
                        #car.vin_code = vin
                        #car.save()
                        return viber.send_messages(vid, quick_create_waybill(vid, car, odometer_value))
            except DCardNotFoundException:
                d_card.number_of_failed_attempts += 1
                if (d_card.number_of_failed_attempts + 1) > 2:
                    d_card.is_active = False
                d_card.save()
                return viber.send_messages(vid,
                                           [TextMessage(
                                               text=f"Вам отказано в получении путевого листа, т.к. отсутствует " \
                                                    f"диагностическая карта, вам необходимо пройти полугодовой " \
                                                    f"технический осмотр ТС.\n\n" \
                                                    f"Проверьте введённый вами ранее VIN-код" \
                                                    f"\n\n{d_card.vin_code}\n\nПри обнаружении ошибки введите его заново. " \
                                                    f"Используются только цифры и символы латинского алфавита, за " \
                                                    f"исключением 'I', 'O' и 'Q'.",
                                               keyboard=entering_vin_kb(car_number, odometer_value),
                                               min_api_version=6)])

            except MissingKeyException:
                text = "Сервис проверки диагностической карты недоступен. "\
                                                    "Повторите попытку позже"
                return viber.send_messages(vid, edit_vin_rich(vid, text, car))
            except BadRequestException:
                text = "Сервис проверки диагностической карты недоступен. " \
                       "Повторите попытку позже"
                return viber.send_messages(vid, edit_vin_rich(vid, text, car))

    elif action_body.startswith('vin-retry'):
        car_number = action_body.split("_")[1]
        odometer_value = action_body.split("_")[2]
        car = Car.objects.get(car_number=car_number)
        d_card = get_d_card(subscriber, car)
        if d_card.number_of_failed_attempts > 2:
            d_card.is_active = False
            d_card.save()
            text = f"Вам отказано в получении путевого листа для автомобиля " \
                   f"{car}, т.к. у вас не пройден техосмотр.\n\n" \
                   f"1) Вам необходимо пройти полугодовой технический осмотр\n" \
                   f"2) Сообщить администратору о наличии актуальной " \
                   f"диагностической карты\n" \
                   f"3) После того как администратор сообщит Вам что " \
                   f"разрешается подтвердить наличие диагностической карты - " \
                   f"нажмите на кнопку \"Подтвердить техосмотр\"\n"
            return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))
        if odometer_value is None:
            viber.send_messages(vid, [KeyboardMessage(keyboard=main_menu_kb(vid), min_api_version=6)])
        else:
            viber.send_messages(vid, notify_for_entering_vin_rich(car_number, odometer_value))

    elif action_body.startswith("confirm-ti"):
        car_number = action_body.split("_")[1]
        confirm_technical_inspection(vid, car_number)
    
    elif action_body == "send-waybill-application":
        if subscriber.is_admin or admissibility_of_receiving_waybill(vid):
            car_number = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid)).tr_reg_num
            car = Car.objects.get(car_number=car_number)
            car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
            if not car.is_available:
                return viber.send_messages(vid, to_menu_kb("Автомобиль " + car_str +
                                                           " заблокирован, вам отказано в получении "
                                                           "путевого листа!"))
            if not car.is_active_license:
                return viber.send_messages(vid, to_menu_kb("Автомобиль " + car_str +
                                       " заблокирован, вам отказано в получении путевого листа!"))
            # viber.send_messages(vid, quick_create_waybill(vid))
            viber.send_messages(vid, quick_create_waybill(vid, car))

    elif action_body == "close-waybill":
        viber.send_messages(vid, [TextMessage(text="Введите показание одометра", min_api_version=6,
                                              tracking_data="set-odometer-for-close-waybill"),
                                  cancel_kb("set-odometer-for-close-waybill")])

    elif tracking_data == "set-odometer-for-close-waybill":
        #        wbn_filter_by_applicant = WaybillNote.objects.filter(applicant=subscriber)
        #        if not wbn_filter_by_applicant.exists():
        #            t = Thread(target=create_note, args=[vid])
        #            t.setDaemon(True)
        #            t.start()
        #            t.join()

        #        time.sleep(0.2)
        #        wbn = wbn_filter_by_applicant.last()
        #        wbn.final_odometer_value = action_body
        #        wbn.save()

        wbe = WaybillEntry.objects.get(applicant=subscriber)
        wbe.closed = True
        wbe.save()
        viber.send_messages(vid, [TextMessage(text="Путевой лист закрыт", keyboard=main_menu_kb(vid),
                                              min_api_version=6)])

    elif action_body == "license_form":
        viber.send_messages(vid,
                            [license_form(vid=vid, number_button=None, text="Заявка на лицензию",
                                          text_field="hidden")])
    elif action_body == "apply_for_a_taxi_permit":
        viber.send_messages(vid, [
            TextMessage(text="Выберите регион", min_api_version=6),
            choice_region_kb()])

    elif action_body in [city.region_name for city in ConditionsForRegions.objects.all()]:
        viber.send_messages(vid, [TextMessage(text=str(conditions(action_body)), min_api_version=6),
                                  send_request_or_come_back()])
    elif action_body.startswith("license"):
        number_button = action_body.split('_')[1]
        text = action_body.split('_')[2]
        viber.send_messages(vid,
                            [license_form(vid=vid, number_button=number_button, text=text,
                                          order_data=number_button, text_field="regular")])
    elif action_body.startswith("waybill"):
        number_button = action_body.split("_")[1]
        text = action_body.split("_")[2]
        viber.send_messages(vid,
                            [waybill_form(vid=vid, number_button=number_button, text=text,
                                          order_data=number_button, text_field="regular")])

    elif action_body == "info":
        if not subscriber.phone:
            viber.send_messages(vid, [get_phone_for_letter()])
        else:
            viber.send_messages(vid, [info()])

    elif action_body.startswith("tariff"):
        ordering.tariff = action_body.split('_')[1]
        ordering.save()
        service = services[ordering.service.split('_')[1]]
        viber.send_messages(vid, [from_address(service)])

    elif action_body.startswith("/back_tariff_"):
        service = action_body.split('_')[2]
        if service == "cargo":
            viber.send_messages(vid, [choice_cargo_tariff()])
        elif service == "evacuator":
            viber.send_messages(vid, [choice_evacuator_tariff()])

    elif action_body == "/back_from":
        service = services[ordering.service.split('_')[1]]
        viber.send_messages(vid, [from_address(service)])

    elif action_body == "/back_to":
        viber.send_messages(vid, [to_address()])

    elif action_body == "/back_comment":
        viber.send_messages(vid, [comment()])

    elif action_body == "/comment" or tracking_data == "/comment":
        com = action_body if action_body != "/comment" else ""
        ordering.comment = com
        ordering.save()
        if not Subscriber.objects.get(user=vid).phone:
            viber.send_messages(vid, [get_phone()])
        else:
            set_order(vid)
    elif action_body == "order":
        unit_id = ordering.service.split('_')[1]
        tariff_id = ordering.tariff
        from_location = ordering.from_location.split('#')[0]
        to_location = ordering.to_location.split('#')[0]

        order_id = send_order(unit_id=unit_id, tariff_id=tariff_id, phone=subscriber.phone,
                              addr_from=from_location, addr_to=to_location,
                              comment=ordering.comment).split(b' ')[2].decode()
        ordering.order_id = order_id
        ordering.save()

        viber.send_messages(vid, messages=[TextMessage(text="Ваш заказ отправлен!"),
                                           cancel_order_or_menu_rich()])
    elif action_body == "cancel_order":
        cancel(ordering.order_id)
        viber.send_messages(vid, messages=[TextMessage(text="Ваш заказ отменён!"),
                                           return_to_menu_rich()])
    elif action_body.startswith("driver"):
        order_id = action_body.split("|")[1]
        order_ = Order.objects.get(order_id=order_id)
        viber.send_messages(vid, [TextMessage(text="Информация о заказе\n" + get_order_string(order_.owner.user)),
                                  take_order_or_not_rich(order_id)])
        keyboard = {"Type": "keyboard",
                    "InputFieldState": 'hidden',
                    "Buttons": order_buttons()
                    }

        viber.send_messages(vid, [KeyboardMessage(keyboard=keyboard, min_api_version=6)])
    elif action_body == "for-drivers":
        viber.send_messages(vid, [KeyboardMessage(keyboard=main_menu_kb(vid),
                                                  min_api_version=6)])
    elif action_body == "get-distance-limited-orders":
        viber.send_messages(vid, [TextMessage(text='Напишите расстояние в км, '
                                                   'в радиусе которого вы хотите видеть заказы',
                                              tracking_data='enter-radius-distance')])

    elif action_body == "get-all-orders":

        keyboard = {"Type": "keyboard",
                    "InputFieldState": 'hidden',
                    "Buttons": order_buttons()
                    }

        viber.send_messages(vid, [to_menu_rich(), KeyboardMessage(keyboard=keyboard, min_api_version=6)])
    elif action_body.startswith("take-order"):
        order_id = action_body.split("|")[1]
        order_ = Order.objects.get(order_id=order_id)
        order_owner_user = order_.owner.user
        order_.ord_success = True
        order_.save()
        viber.send_messages(vid, [TextMessage(text="Через сколько времени Вы прибудете к месту посадки?",
                                              keyboard=driver_arrival_interval(order_owner_user, order_id),
                                              min_api_version=6)])
    elif action_body.startswith("time-interval"):
        a = action_body.split("|")
        order_owner_user = a[2]
        order_id = a[3]
        viber.send_messages(vid, [
            TextMessage(text="Информация о заказе\n" + get_order_string(order_owner_user) + "\nПринять заказ?")])
        viber.send_messages(vid, [KeyboardMessage(keyboard=accept_the_order_or_cancel_kb(order_id), min_api_version=6)])
    elif action_body.startswith("order-cancellation"):
        order_id = action_body.split("|")[1]
        order_ = Order.objects.get(order_id=order_id)
        order_.ord_success = False
        order_.save()
        keyboard = {"Type": "keyboard",
                    "InputFieldState": 'hidden',
                    "Buttons": order_buttons()
                    }

        viber.send_messages(vid, [to_menu_rich(), KeyboardMessage(keyboard=keyboard, min_api_version=6)])

    elif action_body.startswith("accept-order"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [KeyboardMessage(keyboard=after_take_driver_kb(order_id), min_api_version=6)])
    elif action_body.startswith("call-to-client"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [TextMessage(text="Подтверждение\nПозвонить клиенту?",
                                              keyboard=call_or_cancel_kb(order_id),
                                              min_api_version=6)])
    elif action_body.startswith("in-arrival-call-to-client"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [TextMessage(text="Подтверждение\nПозвонить клиенту?",
                                              keyboard=call_or_cancel_in_arrival_moment_kb(order_id),
                                              min_api_version=6)])
    elif action_body.startswith("arrived-at-place"):
        order_id = action_body.split("|")[1]
        order_ = Order.objects.get(order_id=order_id)
        landing_place = order_.from_location.split("#")[0]
        viber.send_messages(vid, [TextMessage(text="Вы уже на месте посадки - \n" + landing_place + " ?",
                                              keyboard=arrival_or_cancel_kb(order_id),
                                              min_api_version=6)])
    elif action_body.startswith("accept-arrival"):
        order_id = action_body.split("|")[1]
        order_ = Order.objects.get(order_id=order_id)
        order_owner_user = order_.owner.user
        viber.send_messages(vid, [TextMessage(text="Информация о заказе\n" + get_order_string(order_owner_user))])
        viber.send_messages(vid, [KeyboardMessage(keyboard=after_accept_arrival_kb(order_id), min_api_version=6)])
    elif action_body.startswith("landing"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [TextMessage(text="Подтверждение\nПоехали?")])
        viber.send_messages(vid, [KeyboardMessage(keyboard=start_trip_or_cancel_kb(order_id), min_api_version=6)])
    elif action_body.startswith("start_trip"):
        order_id = action_body.split("|")[1]
        viber.send_messages(vid, [KeyboardMessage(keyboard=finish_trip_kb(order_id), min_api_version=6)])
    elif action_body.startswith("finish_trip"):
        order_id = action_body.split("|")[1]
        order_ = Order.objects.get(order_id=order_id)
        viber.send_messages(vid, [TextMessage(text="К оплате " + str(order_.order_cost) + " руб.")])
        viber.send_messages(vid, [refresh_menu_rich(), choice_service(vid)])

    elif action_body == "personal-account":
        viber.send_messages(vid, [personal_account_kb()])

    elif action_body == "back-to-cars":
        car = Car.objects.filter(car_owner=Subscriber.objects.get(user=vid)).last()
        car.delete()
        viber.send_messages(vid, [personal_account_kb()])

    elif action_body == "my-cars":
        viber.send_messages(vid, [my_cars(vid)])
    elif action_body == "choice-car":
        viber.send_messages(vid, [list_of_cars(vid, common_list='False')])

    elif action_body.startswith("set-vin-for-my-car"):
        car_number = action_body.split("_")[1]
        car = Car.objects.get(car_number=car_number)
        d_card = get_d_card(subscriber, car)
        tracking_data = f'set-vin-code_{car_number}'
        viber.send_messages(vid, [entering_vin_code_for_car_in_my_list(car, d_card.vin_code),
                                  back_kb("my-cars", tracking_data)])
    elif action_body.startswith("edit-vin-for-my-car"):
        car_number = action_body.split("_")[1]
        car = Car.objects.get(car_number=car_number)
        d_card = get_d_card(subscriber, car)
        tracking_data = f'set-vin-code_{car_number}'
        viber.send_messages(vid, [entering_vin_code_for_car_in_my_list(car, d_card.vin_code),
                                  back_kb("menu", tracking_data)])

    elif action_body.startswith("add-car"):
        car_number_for_add_auto = action_body.split('_')[1]
        adding_car = Car.objects.get(car_number=car_number_for_add_auto)
        car_brand = adding_car.car_brand
        car_model = adding_car.car_model
        car_lic_num = adding_car.car_licensing_number
        return_to_index = action_body.split('_')[2]
        str_after_adding_car = "Вы добавили в свой список автомобилей " + str(car_brand) + " " + \
                               str(car_model) + " " + str(car_number_for_add_auto) + " " + str(car_lic_num)
        subscriber.cars.add(Car.objects.get(car_number=car_number_for_add_auto))
        viber.send_messages(vid, [list_of_cars(vid, str_after_adding_car, index=return_to_index)])
    elif action_body == "return-to-car-list":
        viber.send_messages(vid, [list_of_cars(vid)])

    elif action_body.startswith("/next-cars"):
        next_or_previous(action_body, vid, 'next')
    elif action_body.startswith("/prev-cars"):
        next_or_previous(action_body, vid, 'previous')

    elif action_body == "return_to_choice_car_from_common_list":
        car = Car.objects.filter(car_owner=Subscriber.objects.get(user=vid)).last()
        car.delete()
        viber.send_messages(vid, [list_of_cars(vid, text='', common_list='True')])
    elif action_body.startswith("del-car"):
        car_number_for_del_auto = action_body.split('_')[1]
        car_filter = Car.objects.filter(car_owner=subscriber)
        str_after_deleting_car = ''
        if car_filter.exists():
            deleting_car = Car.objects.get(car_number=car_number_for_del_auto)
            car_brand = deleting_car.car_brand
            car_model = deleting_car.car_model
            car_lic_num = deleting_car.car_licensing_number
            str_after_deleting_car = "Вы удалили из своего списка автомобилей " + str(car_brand) + " " + \
                                     str(car_model) + " " + str(car_number_for_del_auto) + " " + str(car_lic_num)
            subscriber.cars.remove(car_filter.get(car_number=car_number_for_del_auto))

        viber.send_messages(vid, [my_cars(vid, str_after_deleting_car)])
    elif action_body == "wb_car_choice":
        viber.send_messages(vid, choice_from_my_cars(vid, next_to='to-waybill-form'))
    elif action_body.startswith("choice-car"):
        car_number = action_body.split('_')[1]
        next_to = action_body.split('_')[2]
        car = subscriber.cars.get(car_number=car_number)

        d_card = get_d_card(subscriber, car)
        if d_card.checking_dc:
            if d_card.vin_code != '':
                if d_card.number_of_failed_attempts > 0:
                    if d_card.number_of_failed_attempts > 2:
                        text = f"Вам отказано в получении путевого листа для автомобиля " \
                               f"{car}, т.к. у Вас не пройден техосмотр ТС.\n\n" \
                               f"1) Вам необходимо пройти полугодовой технический осмотр ТС\n" \
                               f"2) Сообщить администратору о наличии актуальной " \
                               f"диагностической карты\n" \
                               f"3) После того как администратор сообщит Вам что " \
                               f"разрешается подтвердить наличие диагностической карты - " \
                               f"нажмите на кнопку \"Подтвердить техосмотр\"\n"
                        return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))
                    text = "Вам отказано в получении путевого листа, т.к. " \
                           f"диагностическая карта автомобиля {car} просрочена\n\n" \
                           "1) Вам необходимо пройти полугодовой технический осмотр\n" \
                           "2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
                    return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))
            else:
                d_card.number_of_failed_attempts = 0
                d_card.save()

        if next_to == 'to-quick-create-waybill':
            car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
            if not car.is_available:
                return viber.send_messages(vid, to_menu_kb("Автомобиль " + car_str +
                                                           " заблокирован, вам отказано в получении "
                                                           "путевого листа!"))
            if not car.is_active_license:
                return viber.send_messages(vid, to_menu_kb("Лицензия автомобиля " + car_str +
                                                           " аннулирована, вам отказано в получении "
                                                           "путевого листа!"))
            
            viber.send_messages(vid, quick_create_waybill(vid, car))

        elif next_to == 'to-waybill-form':

            car_brand = car.car_brand
            car_model = car.car_model
            car_lic_num = car.car_licensing_number
            car_vehicle_class = car.vehicle_class
            set_answer_waybill_question(vid, car_number, "5_0")
            set_answer_waybill_question(vid, car_brand, "5_1")
            set_answer_waybill_question(vid, car_model, "5_2")
            set_answer_waybill_question(vid, car_lic_num, "5_3")
            set_answer_waybill_question(vid, car_vehicle_class, "5_4")

            viber.send_messages(vid, [
                waybill_form(vid=vid, number_button=5, text_field="hidden", answered=True)])
    elif action_body.startswith("car-choice-and-add-my-list"):
        car_number = action_body.split('_')[1]
        return_to = action_body.split('_')[2]
        adding_car = Car.objects.get(car_number=car_number)
        car_brand = adding_car.car_brand
        car_model = adding_car.car_model
        car_lic_num = adding_car.car_licensing_number
        car_vehicle_class = adding_car.vehicle_class
        str_after_adding_car = str(car_brand) + " " + \
                               str(car_model) + " " + str(car_number)
        subscriber.cars.add(adding_car)
        set_answer_waybill_question(vid, car_number, "5_0")
        set_answer_waybill_question(vid, car_brand, "5_1")
        set_answer_waybill_question(vid, car_model, "5_2")
        set_answer_waybill_question(vid, car_lic_num, "5_3")
        set_answer_waybill_question(vid, car_vehicle_class, "5_4")
        if return_to == 'to-waybill-form':
            viber.send_messages(vid,
                                [waybill_form(vid=vid, number_button=5, text=str_after_adding_car,
                                              text_field="hidden")])

        elif return_to == 'to-quick-create-waybill':
            odometer_value = wbe_for_subscriber.get().odometer_value
            d_card = get_d_card(subscriber, adding_car)
            if d_card.vin_code == '':
                tracking_data = f'vin-code_{car_number}'
                return viber.send_messages(vid, [
                    TextMessage(text=f"Введите VIN код автомобиля {car_brand} {car_model} {car_number}, "
                                     f"его можно посмотреть как на самом автомобиле, так и в СТС",
                                tracking_data=tracking_data), cancel_kb(tracking_data)])
            else:
                vin = d_card.vin_code
                car_number = adding_car.car_number
                try:
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(check_dc, vin)
                        dc_expiration_date = datetime.strptime(future.result(), '%Y-%m-%d').date()
                        d_card.dc_expiration_date = dc_expiration_date
                        d_card.save()

                        if not check_dc_exp_date(dc_expiration_date) or not d_card.is_active:
                            d_card.number_of_failed_attempts += 1
                            if (d_card.number_of_failed_attempts + 1) > 2:
                                d_card.is_active = False
                            d_card.save()
                            text = "Вам отказано в получении путевого листа, т.к. " \
                                   f"диагностическая карта автомобиля {adding_car} просрочена\n\n" \
                                   "1) Вам необходимо пройти полугодовой технический осмотр\n" \
                                   "2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
                            return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, adding_car))

                        #adding_car.vin_code = vin
                        #adding_car.save()
                        d_card.number_of_failed_attempts = 0
                        d_card.save()

                except DCardNotFoundException:
                    d_card.number_of_failed_attempts += 1
                    if (d_card.number_of_failed_attempts + 1) > 2:
                        d_card.is_active = False
                    d_card.save()
                    return viber.send_messages(vid, [
                        TextMessage(text=f"Вам отказано в получении путевого листа, т.к. отсутствует " \
                                         f"диагностическая карта, вам необходимо пройти полугодовой " \
                                         f"технический осмотр ТС.\n\n" \
                                         f"Проверьте введённый вами ранее VIN-код" \
                                         f"\n\n{d_card.vin_code}\n\nПри обнаружении ошибки введите его заново. " \
                                         f"Используются только цифры и символы латинского алфавита, за " \
                                         f"исключением 'I', 'O' и 'Q'.",
                                    keyboard=entering_vin_kb(car_number, odometer_value),
                                    min_api_version=6)])

                except MissingKeyException:
                    text = "Сервис проверки диагностической карты недоступен. " \
                           "Повторите попытку позже"
                    return viber.send_messages(vid, edit_vin_rich(vid, text, adding_car))
                except BadRequestException:
                    text = "Сервис проверки диагностической карты недоступен. " \
                           "Повторите попытку позже"
                    return viber.send_messages(vid, edit_vin_rich(vid, text, adding_car))
            # url, path_to_pdf, file_name_pdf, user_path = waybill_build(vid)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(waybill_build, vid)
                url, path_to_pdf, file_name_pdf, user_path = future.result()
                executor.submit(create_note, vid)
                # create_note(vid)

                executor.submit(pdf_to_png_converter, str(path_to_pdf))
                # t = Thread(target=pdf_to_png_converter, args=[str(path_to_pdf)])
                # t.start()
                # t.join()
                url_to_image_waybill = url[:-4] + ".png"
                viber.send_messages(vid,
                                    [TextMessage(text="Путевой лист легкового автомобиля\n" +
                                                      get_waybill_answer_string(vid, )),
                                     PictureMessage(media=url_to_image_waybill, min_api_version=6),
                                     to_menu_and_permission_taxi_kb(vid)])

        elif return_to == 'common_list_of_cars':
            viber.send_messages(vid, list_of_cars(vid, common_list='False'))

    elif tracking_data.startswith("set-vin-code"):
        car_number = tracking_data.split("_")[1]
        car = Car.objects.get(car_number=car_number)
        d_card = get_d_card(subscriber, car)
        d_card.vin_code = action_body
        d_card.save()
        str_after_setting_vin_code_car = f"Вы изменили VIN-код для автомобиля {car}"
        viber.send_messages(vid, [my_cars(vid, str_after_setting_vin_code_car)])

    elif tracking_data.startswith('car-search-by-number'):
        query_on_ru_words = parse_car_number(action_body)[0]
        query_on_en_words = parse_car_number(action_body)[1]
        found_cars_by_ru = search_by_car("car_number", query_on_ru_words)
        found_cars_by_en = search_by_car("car_number", query_on_en_words)
        found_cars = list(found_cars_by_ru.union(found_cars_by_en))
        local_storage.update({"cars_" + vid: found_cars})
        common_list = tracking_data.split("_")[1]
        next_to = tracking_data.split("_")[2]

        if len(found_cars) == 0:
            viber.send_messages(vid, list_of_cars(vid, "Автомобиль не найден!\nПопробуйте повторить поиск или выберите "
                                                       "из списка автомобилей", common_list=common_list))
        else:
            viber.send_messages(vid, list_of_cars(vid, found_cars=found_cars, common_list=common_list, next_to=next_to))
    elif action_body == "balance-info":
        viber.send_messages(vid, [to_menu_rich(), TextMessage(text="Информация о балансе\nНа вашем счету ... руб.\n"),
                                  KeyboardMessage(keyboard=balance_kb(), min_api_version=6)])
    elif action_body == "payment-for-car":
        viber.send_messages(vid, [my_cars(vid, text="Нажмите кнопку \"Оплатить\"", payments=True)])
    elif action_body.startswith("https://yoomoney.ru/"):
        return False
    elif action_body.startswith("http"):
        return False

    elif action_body.startswith("self-sending-file-pdf"):
        file_attributes = action_body.split("*")
        url = file_attributes[1]
        path_to_pdf = file_attributes[2]
        t = Thread(target=pdf_to_png_converter, args=[path_to_pdf])
        t.start()
        t.join()
        url_to_image_waybill = url[:-4] + ".png"
        viber.send_messages(vid, [PictureMessage(media=url_to_image_waybill, min_api_version=6), to_menu_rich()])
    elif action_body.startswith("permission-taxi"):
        if subscriber.is_driver:
            quick_create_permission(vid)
        else:
            return viber.send_messages(vid,
                                       TextMessage(
                                           text="Вы заблокированы, для разблокировки свяжитесь с администратором",
                                           keyboard=main_menu_kb(vid),
                                           min_api_version=6))

    elif action_body.startswith("permission"):
        car_number = action_body.split("_")[1]
        send_permission(vid, car_number)


def next_or_previous(action_body, vid, sign):
    if sign == 'next':
        index = int(action_body.split("_")[1])
    else:
        index = int(action_body.split("_")[1]) - 22

    common_list = action_body.split("_")[2]
    next_to = action_body.split("_")[3]

    viber.send_messages(vid, [list_of_cars(vid, index=index, common_list=common_list, next_to=next_to)])


def car_management(vid, car_number, command):
    car_number_filtering = Car.objects.filter(car_number=car_number)
    button_color_and_actions = {}
    if car_number_filtering.exists():
        car = car_number_filtering.get()
        if car.is_available == command:
            return
        
        if car.is_active_license == command:
            return

        car.is_available = command
        car.save()
        if command:
            button_color_and_actions.update({car_number: (bg_color, 'reply')})
            list_of_cars(vid, '', button_color_and_actions)
        else:
            button_color_and_actions.update({car_number: (non_active_button_color, 'none')})
            list_of_cars(vid, '', button_color_and_actions)


def change_color_and_actions_for_car_button(vid, car_number):
    car = Car.objects.get(car_number=car_number)
    if car.is_available:
        car_management(vid, car_number, False)
    else:
        car_management(vid, car_number, True)


def form_thread(vid, action_body, tracking_data, target_func):
    t = Thread(target=target_func, args=[vid, action_body, tracking_data])
    t.setDaemon(True)
    t.start()
    t.join()


def license_app_form_handler(vid, action_body, tracking_data):
    subscriber = Subscriber.objects.get(user=vid)
    id_number = tracking_data.split('_')[1]
    n = id_number if id_number != "" else None
    count = LicensingQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
    answered = True if count == 11 else False
    if not action_body.startswith("license_") and not action_body.startswith("send_") and not action_body == "menu":
        set_answer_licensing_question(vid, action_body, id_number)
    viber.send_messages(vid, [license_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])


def job_app_form_handler(vid, action_body, tracking_data):
    subscriber = Subscriber.objects.get(user=vid)
    id_number = tracking_data.split('_')[1]
    n = id_number if id_number != "" else None
    count = QuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
    answered = True if count == 10 else False
    if not action_body.startswith("job_") and not action_body.startswith("c") and not action_body == "menu":
        set_answer(vid, action_body, id_number)
    viber.send_messages(vid, [job_application_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])


def waybill_form_handler(vid, action_body, tracking_data):
    subscriber = Subscriber.objects.get(user=vid)
    id_number = tracking_data.split("_")[1]
    n = id_number if id_number != "" else None
    if WaybillQuestionnaireButtons.objects.get(user=subscriber).edit:
        if not action_body.startswith("waybill_") \
                and not action_body.startswith("send-") \
                and not action_body == "for-drivers" \
                and not action_body == "wb_car_choice" \
                and not action_body == "personal-account" \
                and not action_body == "verify-data" \
                and not action_body == "set-snils":
            res = set_answer_waybill_question(vid, action_body, id_number)
            if str(res).startswith("retry"):
                number_retry = res.split("_")[1]

                text = res.split("_")[2]
                viber.send_messages(vid,
                                    [waybill_form(vid=vid, number_button=number_retry, text=text,
                                                  text_field="regular", data="retry", answered=True)])
            else:
                viber.send_messages(vid,
                                    [waybill_form(vid=vid, number_button=n, text_field="hidden", answered=True)])
    else:
        count = WaybillQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(action_type="none").count()
        answered = True if count == 9 else False
        if not action_body.startswith("waybill_") \
                and not action_body.startswith("send-") \
                and not action_body == "for-drivers" \
                and not action_body == "wb_car_choice" \
                and not action_body == "personal-account" \
                and not action_body == "verify-data" \
                and not action_body == "set-snils":
            res = set_answer_waybill_question(vid, action_body, id_number)
            if str(res).startswith("retry"):
                number_retry = res.split("_")[1]
                text = res.split("_")[2]
                viber.send_messages(vid,
                                    [waybill_form(vid=vid, number_button=number_retry, text=text,
                                                  text_field="regular", data="retry", answered=True)])
            else:
                viber.send_messages(vid, [
                    waybill_form(vid=vid, number_button=n, text_field="hidden", answered=answered)])


def set_tz(data):
    msk_gmt = 3
    offset = timedelta(hours=msk_gmt)
    msk_tz = timezone(offset, name='MSK')
    now_in_msk = datetime.now(tz=msk_tz)
    hours_in_msk = datetime.time(now_in_msk).strftime("%H")
    splitter = re.compile(r'\s*[:,.\-_\s]\s*')

    hours_in_client_tz = re.split(splitter, data)[0]
    hours_diff = int(hours_in_client_tz) - int(hours_in_msk)
    time_zone = msk_gmt + hours_diff
    if time_zone > 14:
        d = time_zone - 14
        time_zone = d - 12
    return time_zone


def waybill_build(vid, odometer_value=None, car: Car = None):
    is_exists_waybill_questionnaire(vid)
    subscriber = Subscriber.objects.get(user=vid)
    wbe = WaybillEntry.objects.get(applicant=subscriber)

    wbe.counter += 1

    journal = get_journal()
    increment = journal.journal_counter + 1

    offset = timedelta(hours=int(wbe.time_zone))
    tz = timezone(offset, name='TZ')
    now = datetime.now(tz=tz)
    datetime_date = datetime.date(now).strftime("%d.%m.%Y")
    datetime_time = datetime.time(now).strftime("%H-%M")
    wbe.time = datetime_time
    wbe.date = datetime_date

    wbe.save()

    if odometer_value is not None:
        odometer_val = odometer_value
        wbe.odometer_value = odometer_value
    else:
        odometer_val = wbe.odometer_value

    if car is not None:
        car_mark = car.car_brand + " " + car.car_model
        car_num = car.car_number
        car_vehicle_class = car.vehicle_class

        se = SelfEmployed.objects.filter(user=subscriber)
        if se.exists() and CarFileDocumentPairIntermediate.objects.filter(self_employed=se.get()).filter(
                car=car).exists():
            car_organization: SelfEmployed = se.get()
        else:
            car_organization: Organization = car.organization

        if car_organization is None:
            return viber.send_messages(vid,
                                       [TextMessage(text=f"Автомобиль {car} не пренадлежит ни одной из организаций,"
                                                         f" сообщите об этом администратору",
                                                    keyboard=main_menu_kb(vid), min_api_version=6)])

        wbe.tr_mark = car.car_brand
        wbe.tr_model = car.car_model
        wbe.tr_reg_num = car.car_number
        wbe.num_lic = car.car_licensing_number
        wbe.kod_org_doc = car.vehicle_class
        wbe.organization = car.organization
    else:
        car_mark = wbe.tr_mark + " " + wbe.tr_model
        car_num = wbe.tr_reg_num
        car_vehicle_class = wbe.kod_org_doc
        car_organization = wbe.organization

    snils = subscriber.SNILS

    user_path, usr_dir_name, path_to_pdf, file_name_pdf, attach_data = \
        render_pdf_template(vid=vid, number=increment, id_client=increment,
                            time=wbe.time, date=wbe.date,
                            surname=wbe.surname, name=wbe.name,
                            patronymic=wbe.patronymic, ser_doc=wbe.ser_doc,
                            num_doc=wbe.num_doc,
                            snils=snils,
                            kod_org_doc=car_vehicle_class,
                            tr_mark=car_mark,
                            tr_reg_num=car_num,
                            odometer_value=odometer_val,

                            car_organization_name=car_organization.name,
                            car_organization_contract_number=car_organization.contract_number,
                            car_organization_eds_org_name=car_organization.EDS_org_name,
                            car_organization_eds_valid_from=car_organization.EDS_valid_from.strftime("%d.%m.%Y"),
                            car_organization_eds_valid_to=car_organization.EDS_valid_to.strftime("%d.%m.%Y"),
                            car_organization_inn=car_organization.INN,
                            car_organization_ogrn=car_organization.OGRN,

                            car_organization_mechanic=car_organization.mechanic.get_mechanic_fio(),
                            car_organization_mechanic_eds_valid_from=car_organization.mechanic.EDS_valid_from.strftime(
                                "%d.%m.%Y"),
                            car_organization_mechanic_eds_valid_to=car_organization.mechanic.EDS_valid_to.strftime(
                                "%d.%m.%Y"),
                            car_organization_mechanic_eds_number=car_organization.mechanic.EDS_number,
                            car_organization_mechanic_eds_address=car_organization.mechanic.EDS_address,

                            car_organization_dispatcher=car_organization.dispatcher.get_dispatcher_fio(),
                            car_organization_dispatcher_eds_valid_from=car_organization.dispatcher.EDS_valid_from.strftime(
                                "%d.%m.%Y"),
                            car_organization_dispatcher_eds_valid_to=car_organization.dispatcher.EDS_valid_to.strftime(
                                "%d.%m.%Y"),
                            car_organization_dispatcher_eds_number=car_organization.dispatcher.EDS_number,
                            car_organization_dispatcher_eds_address=car_organization.dispatcher.EDS_address,

                            car_organization_doctor=car_organization.doctor.get_doctor_fio(),
                            car_organization_doctor_eds_valid_from=car_organization.doctor.EDS_valid_from.strftime(
                                "%d.%m.%Y"),
                            car_organization_doctor_eds_valid_to=car_organization.doctor.EDS_valid_to.strftime(
                                "%d.%m.%Y"),
                            car_organization_doctor_eds_number=car_organization.doctor.EDS_number,
                            car_organization_doctor_eds_address=car_organization.doctor.EDS_address,
                            )

    wbe.number = increment
    wbe.id_client = increment
    wbe.path_to_pdf_version = Path(path_to_pdf)
    wbe.closed = False
    wbe.save()
    url = server_url + MEDIA_URL + usr_dir_name + '/' + str(file_name_pdf)
    # url = server_url + STATIC_URL + usr_dir_name + '/' + str(file_name_pdf)
    return url, path_to_pdf, file_name_pdf, user_path


def save_waybill_to_journal():
    journal = get_journal()
    journal.journal_counter += 1
    journal.save()


def set_edit_waybill_buttons(vid, state):
    is_exists_waybill_buttons(vid)
    waybill_questionnaire_buttons = WaybillQuestionnaireButtons.objects.get(user=Subscriber.objects.get(user=vid))
    waybill_questionnaire_buttons.edit = state
    waybill_questionnaire_buttons.save()


def get_journal():
    journal_objects = WaybillJournal.objects
    if not journal_objects.exists():
        journal = journal_objects.create()
    else:
        journal = journal_objects.get()
    return journal


def set_order(vid):
    subscriber = Subscriber.objects.get(user=vid)
    is_exists_order(vid)
    ordering = Order.objects.get(owner=subscriber)
    unit_id = ordering.service.split("_")[1]
    tariff_id = ordering.tariff

    from_location = ordering.from_location.split("#")[1]
    to_location = ordering.to_location.split("#")[1]
    lat_from = from_location.split(" ")[0]
    lon_from = from_location.split(" ")[1]
    lat_to = to_location.split(" ")[0]
    lon_to = to_location.split(" ")[1]
    try:
        dist_map = distance(unit_id, tariff_id, lat_from, lon_from, lat_to, lon_to)
        dist = dist_map["distance"]
        price = dist_map["fix_price"]
        ordering.order_cost = price
        ordering.save()
        order_str = get_order_string(vid) + "\n" + "Расстояние: " + str(dist) + " км\n" + "Стоимость: " + \
                    str(price) + " руб."
        viber.send_messages(vid, messages=[TextMessage(text=order_str), KeyboardMessage(keyboard=order_kb(),
                                                                                        min_api_version=6)])
    except Exception:
        error_str = "Во время построения маршрута произошла ошибка!\n\nПопробуйте ещё раз"
        service = services[ordering.service.split("_")[1]]
        return viber.send_messages(vid, [TextMessage(text=error_str), from_address(service)])


def location_handler(*args):
    vid = args[0]
    lat = args[2]
    lon = args[3]
    track = args[4]
    subscriber = Subscriber.objects.get(user=vid)
    is_exists_order(vid)
    ordering = Order.objects.get(owner=subscriber)
    address = get_address(lat, lon)
    address_str = address.split("#")[0]
    if track == "from":
        ordering.from_location = address
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место отправления:\n" + address_str), to_address()])
    elif track == "to":
        ordering.to_location = address
        ordering.save()
        viber.send_messages(vid, [TextMessage(text="Место прибытия:\n" + address_str), comment()])
    elif track.startswith("radius_distance"):
        radius_distance = track.split("|")[1]
        keyboard = {"Type": "keyboard",
                    "InputFieldState": "hidden",
                    "Buttons": order_buttons(lat, lon, radius_distance)
                    }
        viber.send_messages(vid, [to_menu_rich(), KeyboardMessage(keyboard=keyboard, min_api_version=6)])


def picture_handler(viber_request):
    tracking_data = viber_request.message.tracking_data
    vid = viber_request.sender.id
    subscriber = Subscriber.objects.get(user=vid)
    name = viber_request.sender.name
    img_u = viber_request.message.thumbnail
    r = requests.get(img_u)
    path_to_media = Path(MEDIA_ROOT)
    if not Path.exists(path_to_media):
        Path.mkdir(path_to_media)
    v = str(vid)
    user_dir_name = str(v).replace("/", "").replace("+", "").replace("=", "")
    user_path = path_to_media.joinpath(user_dir_name)
    if not Path.exists(user_path):
        Path.mkdir(user_path)
    if tracking_data.startswith("license-app-form_"):
        index = str(tracking_data).split("_")[1]
        str_to_photo = names_for_files.get(index) + ".jpg"
        photo_filename = Path(str_to_photo)
        media_file = user_path.joinpath(photo_filename)
        with open(media_file, "wb") as f:
            f.write(r.content)
        set_answer_licensing_question(vid, media_file, index)
        subscriber = Subscriber.objects.get(user=vid)
        count = LicensingQuestionnaireButtons.objects.get(user=subscriber).buttons.filter(
            action_type="none").count()
        answered = True if count == 11 else False
        viber.send_messages(vid, [license_form(vid=vid, number_button=index, text_field="hidden",
                                               answered=answered, data=str(photo_filename))])
    elif tracking_data == "support_letter":
        str_to_photo = "image_for_support.jpg"
        photo_filename = Path(str_to_photo)
        media_file = user_path.joinpath(photo_filename)
        with open(media_file, "wb") as f:
            f.write(r.content)
        sender = str(name) + " " + str(subscriber.phone)
        send_email(subject="Письмо в техподдержку от " + sender, body_text="Письмо с прикреплённым файлом",
                   files_to_attach=[media_file])
        viber.send_messages(vid, [TextMessage(text="Ваше сообщение отправлено в техподдержку", min_api_version=6),
                                  info()])


def file_handler(request):
    pass


def get_d_card(subscriber, car):
    d_card = DCard.objects.filter(owner=subscriber, car=car)
    if not d_card.exists():
        return DCard.objects.create(owner=subscriber, car=car)
    return d_card.get()


def confirm_technical_inspection(vid, car_number):
    subscriber = Subscriber.objects.get(user=vid)
    car = Car.objects.get(car_number=car_number)
    d_card = get_d_card(subscriber, car)
    try:
        vin = d_card.vin_code
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(check_dc, vin)
            dc_expiration_date = datetime.strptime(future.result(), '%Y-%m-%d').date()
            d_card.dc_expiration_date = dc_expiration_date
            d_card.save()

            if not check_dc_exp_date(dc_expiration_date) or not d_card.is_active:

                d_card.number_of_failed_attempts += 1
                d_card.save()
                if d_card.number_of_failed_attempts > 2:
                    d_card.is_active = False
                    d_card.save()
                    text = f"Информация о пройденом техосмотре транспортного " \
                           f"средства {car} не подтверждена\n\n" \
                           f"1) Вам необходимо пройти полугодовой технический осмотр ТС\n" \
                           f"2) Сообщить администратору о наличии актуальной " \
                           f"диагностической карты\n" \
                           f"3) После того как администратор сообщит Вам что " \
                           f"разрешается подтвердить наличие диагностической карты - " \
                           f"нажмите на кнопку \"Подтвердить техосмотр\"\n"
                    return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))
                text = f"Информация о пройденом техосмотре транспортного " \
                       f"средства {car} не подтверждена\n\n" \
                       "1) Вам необходимо пройти полугодовой технический осмотр\n" \
                       "2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
                return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))

            #car.vin_code = d_card.vin_code
            #car.save()

            subscriber.is_driver = True
            subscriber.save()
            d_card.number_of_failed_attempts = 0
            d_card.save()

            return viber.send_messages(vid, TextMessage(
                text="Вы подтвердили прохождение техосмотра",
                keyboard=main_menu_kb(vid),
                min_api_version=6))
    except DCardNotFoundException:
        d_card.number_of_failed_attempts += 1
        d_card.save()
        if d_card.number_of_failed_attempts > 2:
            d_card.is_active = False
            d_card.save()
            text = f"Информация о пройденом техосмотре транспортного " \
                   f"средства {car} не подтверждена\n\n" \
                   f"1) Вам необходимо пройти полугодовой технический осмотр ТС\n" \
                   f"2) Сообщить администратору о наличии актуальной " \
                   f"диагностической карты\n" \
                   f"3) После того как администратор сообщит Вам что " \
                   f"разрешается подтвердить наличие диагностической карты - " \
                   f"нажмите на кнопку \"Подтвердить техосмотр\"\n"
            return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))
        text = f"Информация о пройденом техосмотре транспортного " \
               f"средства {car} не подтверждена\n\n" \
               "1) Вам необходимо пройти полугодовой технический осмотр\n" \
               "2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
        return viber.send_messages(vid, confirm_diagnostic_card_rich(vid, text, car))

    except MissingKeyException:
        text = "Сервис проверки диагностической карты недоступен. " \
               "Повторите попытку позже"
        return viber.send_messages(vid, edit_vin_rich(vid, text, car))
    except BadRequestException:
        text = "Сервис проверки диагностической карты недоступен. " \
               "Повторите попытку позже"
        return viber.send_messages(vid, edit_vin_rich(vid, text, car))


def quick_create_waybill(vid, car=None, odometer_value=None):
    subscriber = Subscriber.objects.get(user=vid)
    d_card = get_d_card(subscriber, car)
    if d_card.checking_dc:
        if d_card.vin_code == '':
            tracking_data = f'vin-code_{car.car_number}'
            return [TextMessage(text=f"Введите VIN код автомобиля {car.car_brand} {car.car_model} {car.car_number}, "
                                     f"его можно посмотреть как на самом автомобиле, так и в СТС",
                                tracking_data=tracking_data), cancel_kb(tracking_data)]
        else:
            vin = d_card.vin_code
            car_number = car.car_number
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(check_dc, vin)
                    dc_expiration_date = datetime.strptime(future.result(), '%Y-%m-%d').date()
                    d_card.dc_expiration_date = dc_expiration_date
                    d_card.save()

                    if not check_dc_exp_date(dc_expiration_date) or not d_card.is_active:
                        d_card.number_of_failed_attempts += 1
                        if (d_card.number_of_failed_attempts + 1) > 2:
                            d_card.is_active = False
                        d_card.save()
                        text = "Вам отказано в получении путевого листа, т.к. " \
                               f"диагностическая карта автомобиля {car} просрочена\n\n" \
                               "1) Вам необходимо пройти полугодовой технический осмотр\n" \
                               "2) Нажать на кнопку \"Подтвердить техосмотр\"\n\n"
                        return confirm_diagnostic_card_rich(vid, text, car)
                    #car.vin_code = d_card.vin_code
                    #car.save()

                    d_card.number_of_failed_attempts = 0
                    d_card.save()

            except DCardNotFoundException:
                d_card.number_of_failed_attempts += 1
                d_card.save()
                if d_card.number_of_failed_attempts > 2:
                    d_card.is_active = False
                    d_card.save()
                return [TextMessage(text=f"Вам отказано в получении путевого листа, т.к. отсутствует " \
                                         f"диагностическая карта, вам необходимо пройти полугодовой " \
                                         f"технический осмотр ТС.\n\n" \
                                         f"Проверьте введённый вами ранее VIN-код" \
                                         f"\n\n{d_card.vin_code}\n\nПри обнаружении ошибки введите его заново. " \
                                         f"Используются только цифры и символы латинского алфавита, за " \
                                         f"исключением 'I', 'O' и 'Q'.",
                                    keyboard=entering_vin_kb(car_number, odometer_value),
                                    min_api_version=6)]

            except MissingKeyException:
                text = "Сервис проверки диагностической карты недоступен. " \
                       "Повторите попытку позже"
                return edit_vin_rich(vid, text, car)
            except BadRequestException:
                text = "Сервис проверки диагностической карты недоступен. " \
                       "Повторите попытку позже"
                return edit_vin_rich(vid, text, car)

    d_card.number_of_failed_attempts = 0
    d_card.save()
    
    #if d_card.series_and_number_pts == '':
    #    tracking_data = f'pts-series-number_{car.car_number}_{d_card.vin_code}'
    #    return [where_get_pts(tracking_data),
    #            TextMessage(text=f"Введите серию и номер ПТС автомобиля {car.car_brand} {car.car_model} {car.car_number}",
    #                    tracking_data=tracking_data), cancel_kb(tracking_data)]
                        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(waybill_build, vid, odometer_value, car)
        url, path_to_pdf, file_name_pdf, user_path = future.result()
        executor.submit(create_note, vid)
        executor.submit(pdf_to_png_converter, str(path_to_pdf))
    #

    # thread_create_note = Thread(target=create_note, args=[vid])
    # thread_create_note.setDaemon(True)
    #
    # thread_converter = Thread(target=pdf_to_png_converter, args=[str(path_to_pdf)])
    # thread_converter.setDaemon(True)
    #
    # thread_create_note.start()
    # thread_converter.start()
    #
    # thread_create_note.join()
    # thread_converter.join()

    url_to_image_waybill = url[:-4] + ".png"
    return [TextMessage(text="Путевой лист легкового автомобиля\n" + get_waybill_answer_string(vid)),
            PictureMessage(media=url_to_image_waybill, min_api_version=6), to_menu_and_permission_taxi_kb(vid)]


#def quick_create_waybill(vid, car=None, odometer_value=None):
#
#    with concurrent.futures.ThreadPoolExecutor() as executor:
#        future = executor.submit(waybill_build, vid, odometer_value, car)
#        url, path_to_pdf, file_name_pdf, user_path = future.result()
#        executor.submit(create_note, vid)
#        executor.submit(pdf_to_png_converter, str(path_to_pdf))
#
#    url_to_image_waybill = url[:-4] + ".png"
#    return [TextMessage(text="Путевой лист легкового автомобиля\n" + get_waybill_answer_string(vid)),
#            PictureMessage(media=url_to_image_waybill, min_api_version=6), to_menu_and_permission_taxi_kb(vid)]


def quick_create_permission(vid):
    subscriber = Subscriber.objects.get(user=vid)
    my_cars_filter = Car.objects.filter(car_owner=subscriber)
    if my_cars_filter.exists():
        if my_cars_filter.count() == 1:
            car = my_cars_filter.get()
            if not car.is_available:
                car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
                return viber.send_messages(vid, [TextMessage(text='Ваш автомобиль ' + car_str + ' заблокирован'),
                                                 to_menu_and_permission_taxi_kb(vid)])
            if not car.permission:
                car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
                return viber.send_messages(vid, [TextMessage(text='У вас нет разрешения для автомобиля ' + car_str),
                                                 to_menu_and_permission_taxi_kb(vid)])
            if not car.permission_pdf.name:
                sending_permission_for_driver_without_pdf(car, vid)
            else:
                converting_and_sending_permission_pdf(car, vid)
        else:
            list_of_my_cars_with_permission = []
            for car in my_cars_filter.all():
                if not car.permission:
                    list_of_my_cars_with_permission.append(("У вас нет разрешения для ", car, " в электронном виде"))
                    continue
                list_of_my_cars_with_permission.append(car)

            if len(list_of_my_cars_with_permission) == 0:
                viber.send_messages(vid, [TextMessage(text='У вас нет разрешения ни на один из ваших автомобилей'),
                                          to_menu_and_permission_taxi_kb(vid)])
            if len(list_of_my_cars_with_permission) == 1:
                converting_and_sending_permission_pdf(*list_of_my_cars_with_permission, vid)
            if len(list_of_my_cars_with_permission) > 1:
                viber.send_messages(vid, permission_for_cars_buttons(list_of_my_cars_with_permission))

    else:
        viber.send_messages(vid, [TextMessage(text='Вы не выбрали автомобиль в личном кабинете'), to_menu_rich()])


def converter_thread(path_to_pdf):
    # thread_converter = Thread(target=pdf_to_png_converter, args=[str(path_to_pdf)])
    # thread_converter.setDaemon(True)
    # thread_converter.start()
    # thread_converter.join()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(pdf_to_png_converter, str(path_to_pdf))


def create_note(vid):
    save_waybill_to_journal()
    wbe = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid))
    WaybillNote.objects.create(applicant=wbe.applicant,
                               organization=wbe.organization,
                               number=wbe.number,
                               id_client=wbe.id_client,
                               surname=wbe.surname,
                               name=wbe.name,
                               patronymic=wbe.patronymic,
                               ser_doc=wbe.ser_doc,
                               num_doc=wbe.num_doc,
                               num_lic=wbe.num_lic,
                               kod_org_doc=wbe.kod_org_doc,
                               tr_reg_num=wbe.tr_reg_num,
                               tr_mark=wbe.tr_mark,
                               tr_model=wbe.tr_model,
                               odometer_value=wbe.odometer_value,
                               date=wbe.date,
                               time=wbe.time,
                               time_zone=wbe.time_zone)


def send_permission(vid, car_number):
    car = Car.objects.get(car_number=car_number)
    if car.permission_pdf.name:
        converting_and_sending_permission_pdf(car, vid)
    else:
        sending_permission_for_driver_without_pdf(car, vid)


def converting_and_sending_permission_pdf(car, vid):
    if not car.is_available:
        car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
        return viber.send_messages(vid, [TextMessage(text='Ваш автомобиль ' + car_str + ' заблокирован!'),
                                         to_menu_and_permission_taxi_kb(vid)])
    if car.expired_date() >= datetime.now().date():
        path_to_permission_pdf = Path(MEDIA_ROOT).joinpath(str(car.permission_pdf))
        url_permission_pdf = server_url + MEDIA_URL + str(car.permission_pdf)
        converter_thread(path_to_permission_pdf)

        url_to_image_permission = url_permission_pdf[:-4] + ".png"

        car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
        viber.send_messages(vid, [TextMessage(text="Разрешение такси для " + car_str + " действительно до " +
                                                   str(car.expired_date().strftime("%d.%m.%Y"))),
                                  PictureMessage(media=url_to_image_permission, min_api_version=6)])
        send_carrier_document(car, vid)
        viber.send_messages(vid, [to_menu_and_permission_taxi_kb(vid)])
    else:
        viber.send_messages(vid, [TextMessage(text="Срок действия разрешения такси истёк!"),
                                  to_menu_and_permission_taxi_kb(vid)])


def sending_permission_for_driver_without_pdf(car, vid):
    if not car.is_available:
        car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
        return viber.send_messages(vid, [TextMessage(text='Ваш автомобиль ' + car_str + ' заблокирован!'),
                                         to_menu_and_permission_taxi_kb(vid)])
    if car.expired_date() >= datetime.now().date():

        car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
        viber.send_messages(vid, [TextMessage(text="Разрешение такси для " + car_str + " действительно до " +
                                                   str(car.expired_date().strftime("%d.%m.%Y") +
                                                       ".\n\nВ электронном виде не представлено"), min_api_version=6)])
        send_carrier_document(car, vid)
        viber.send_messages(vid, [to_menu_and_permission_taxi_kb(vid)])
    else:
        viber.send_messages(vid, [TextMessage(text="Срок действия разрешения такси истёк!"),
                                  to_menu_and_permission_taxi_kb(vid)])


def send_carrier_document(car, vid):
    se = SelfEmployed.objects.filter(user=Subscriber.objects.get(user=vid))
    if se.exists() and CarFileDocumentPairIntermediate.objects.filter(self_employed=se.get()).filter(car=car).exists():
        permission = CarFileDocumentPairIntermediate.objects.get(self_employed=se.get(), car=car)

        path_to_carrier_pdf = Path(MEDIA_ROOT).joinpath(str(permission))
        url_carrier_pdf = server_url + MEDIA_URL + str(permission)
        converter_thread(path_to_carrier_pdf)
        url_to_image_carrier = url_carrier_pdf[:-4] + ".png"
        viber.send_messages(vid, [TextMessage(text="Разрешение водителя"),
                                  PictureMessage(media=url_to_image_carrier, min_api_version=6)])
    elif car.organization is None:
        return viber.send_messages(vid, TextMessage(text="Разрешение перевозчика не представлено в электронном виде"))
    elif car.organization.carrier_pdf.name:
        path_to_carrier_pdf = Path(MEDIA_ROOT).joinpath(str(car.organization.carrier_pdf))
        url_carrier_pdf = server_url + MEDIA_URL + str(car.organization.carrier_pdf)
        converter_thread(path_to_carrier_pdf)
        url_to_image_carrier = url_carrier_pdf[:-4] + ".png"
        viber.send_messages(vid, [TextMessage(text="Разрешение перевозчика"),
                                  PictureMessage(media=url_to_image_carrier, min_api_version=6)])
    else:
        viber.send_messages(vid, TextMessage(text="Разрешение перевозчика не представлено в электронном виде"))


def admissibility_of_receiving_waybill(vid):
    wbe = WaybillEntry.objects.get(applicant=Subscriber.objects.get(user=vid))
    offset = timedelta(hours=int(wbe.time_zone))
    tz = timezone(offset, name='TZ')

    if wbe.counter > 3:
        t = wbe.time.split("-")
        d = wbe.date.split(".")
        year, month, day = int(d[2]), int(d[1]), int(d[0])
        hours, minutes = int(t[0]), int(t[1])
        previous_time_call_waybill = datetime(year, month, day, hours, minutes, tzinfo=tz)
        next_allowed_time = previous_time_call_waybill + relativedelta(hours=12)
        date_time_now = datetime.now(tz=tz).replace(microsecond=0)

        if next_allowed_time > date_time_now:  # убрать  + relativedelta(hours=13)
            text_msg = f'С момента получения путевого листа прошло менее 12 часов, ' \
                       f'предыдущий был запрошен {previous_time_call_waybill.strftime("%d.%m.%Y в %H-%M")}. ' \
                       f'\n\nПолучение путевого листа станет вновь доступным {next_allowed_time.strftime("%d.%m.%Y с %H-%M")}'
            viber.send_messages(vid, TextMessage(text=text_msg, min_api_version=6, keyboard=main_menu_kb(vid)))
            return False

        if not wbe.closed:
            text_msg = "Ваш предыдущий путевой лист не закрыт, для закрытия путевого листа нажмите кнопку " \
                       "\"Закрыть путевой лист\" после чего введите текущее показание одометра"
            viber.send_messages(vid, [TextMessage(text=text_msg, min_api_version=6, keyboard=close_waybill_kb())])
            return False

    return True


def verify_registration_data(vid):
    subscriber = Subscriber.objects.get(user=vid)
    wbe_filter = WaybillEntry.objects.filter(applicant=subscriber)
    if wbe_filter.exists():
        wbe = wbe_filter.get()
        data = {'surname': [wbe.surname, "фамилия"],
                'name': [wbe.name, "имя"],
                "ser_doc": [wbe.ser_doc, "серия удостоверения"],
                "num_doc": [wbe.num_doc, "номер удостоверения"],
                "reg_num": [wbe.tr_reg_num, "автомобиль"],
                "СНИЛС": [subscriber.SNILS, "СНИЛС"],
                }
        verify = True
        list_of_blank_fields = []
        for item in data.items():
            if item[1][0] == '':
                list_of_blank_fields.append(item[1][1])
                verify = False
        return verify, list_of_blank_fields
