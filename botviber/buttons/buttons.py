import json
import requests
from viberbot.api.messages import RichMediaMessage, TextMessage, KeyboardMessage, FileMessage

import properties
from botviber.models import QuestionnaireButtons, ConditionsForRegions, LicensingQuestionnaireButtons, \
    WaybillQuestionnaireButtons
from HelloDjango.get_distance import is_appropriate_address
from customer.models import Subscriber
from order.models import Order, Car, WaybillEntry

bg_color = "#008B8B"
text_color = "#FFFFFF"
non_active_button_color = "#A9A9A9"

cast = "https://chatapi.viber.com/pa/broadcast_message"
headers = {"X-Viber-Auth-Token": properties.auth_token}

payed = "https://yoomoney.ru/quickpay/shop-widget?writer=buyer&targets=DOGOVOR&targets-hint=DOGOVOR&default-sum=&button-text=11&hint=&successURL=https://........."


def sort_by_car(car):
    return car.car_brand


def is_exists_buttons(vid):
    s = Subscriber.objects.get(user=vid)
    if not QuestionnaireButtons.objects.filter(user=s).exists():
        QuestionnaireButtons.objects.create(user=s)
        question_buttons = QuestionnaireButtons.objects.get(user=s)
        question_buttons.create_buttons()


def is_exists_licensing_buttons(vid):
    s = Subscriber.objects.get(user=vid)
    if not LicensingQuestionnaireButtons.objects.filter(user=s).exists():
        LicensingQuestionnaireButtons.objects.create(user=s)
        licensing_question_buttons = LicensingQuestionnaireButtons.objects.get(user=s)
        licensing_question_buttons.create_buttons()


def is_exists_waybill_buttons(vid):
    s = Subscriber.objects.get(user=vid)
    if not WaybillQuestionnaireButtons.objects.filter(user=s).exists():
        WaybillQuestionnaireButtons.objects.create(user=s)
        waybill_question_buttons = WaybillQuestionnaireButtons.objects.get(user=s)
        waybill_question_buttons.create_buttons()


def set_button(vid, but_id, answered=False):
    subscriber = Subscriber.objects.get(user=vid)
    questionnaire_buttons = QuestionnaireButtons.objects.get(user=subscriber)
    button = questionnaire_buttons.buttons.get(button_id=but_id)
    button.bg_color = non_active_button_color
    button.action_type = "none"
    button.save()
    if answered:
        button = questionnaire_buttons.buttons.get(button_id="9")
        button.bg_color = bg_color
        button.action_type = "reply"
        button.save()
    questionnaire_buttons.save()
    return button.action_body


def set_license_button(vid, but_id, answered=False):
    subscriber = Subscriber.objects.get(user=vid)
    license_questionnaire_buttons = LicensingQuestionnaireButtons.objects.get(user=subscriber)
    button = license_questionnaire_buttons.buttons.get(button_id=but_id)
    button.bg_color = non_active_button_color
    button.action_type = "none"
    button.save()
    if answered:
        button = license_questionnaire_buttons.buttons.get(button_id="10")
        button.bg_color = bg_color
        button.action_type = "reply"
        button.save()
    license_questionnaire_buttons.save()
    return button.action_body


def set_waybill_button(vid, but_id, answered=False):
    subscriber = Subscriber.objects.get(user=vid)
    waybill_questionnaire_buttons = WaybillQuestionnaireButtons.objects.get(user=subscriber)
    button = waybill_questionnaire_buttons.buttons.get(button_id=but_id)
    button.bg_color = non_active_button_color
    button.action_type = "none"
    button.save()
    if answered:
        button = waybill_questionnaire_buttons.buttons.get(button_id="8")
        button.bg_color = bg_color
        button.action_type = "reply"
        button.save()
    waybill_questionnaire_buttons.save()
    return button.action_body


def activate_waybill_button(vid, but_id):
    subscriber = Subscriber.objects.get(user=vid)
    waybill_questionnaire_buttons = WaybillQuestionnaireButtons.objects.get(user=subscriber)
    button = waybill_questionnaire_buttons.buttons.get(button_id=but_id)
    if button.action_type == "reply":
        return button.action_body
    else:
        button.action_type = "reply"
        button.bg_color = bg_color
    button.save()
    waybill_questionnaire_buttons.save()
    return button.action_body


def set_default_buttons(vid):
    subscriber = Subscriber.objects.get(user=vid)
    questionnaire_buttons = QuestionnaireButtons.objects.get(user=subscriber)

    for i in ("0", "1", "2", "3", "4", "5", "6", "7", "8",):
        button = questionnaire_buttons.buttons.get(button_id=i)
        button.bg_color = bg_color
        button.action_type = "reply"
        button.save()
    button = questionnaire_buttons.buttons.get(button_id="9")
    button.bg_color = non_active_button_color
    button.action_type = "none"
    button.save()
    questionnaire_buttons.save()


def set_default_license_buttons(vid):
    subscriber = Subscriber.objects.get(user=vid)
    license_questionnaire_buttons = LicensingQuestionnaireButtons.objects.get(user=subscriber)

    for i in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9",):
        button = license_questionnaire_buttons.buttons.get(button_id=i)
        button.bg_color = bg_color
        button.action_type = "reply"
        button.save()
    button = license_questionnaire_buttons.buttons.get(button_id="10")
    button.bg_color = non_active_button_color
    button.action_type = "none"
    button.save()
    license_questionnaire_buttons.save()


def set_default_waybill_buttons(vid):
    subscriber = Subscriber.objects.get(user=vid)
    waybill_questionnaire_buttons = WaybillQuestionnaireButtons.objects.get(user=subscriber)

    for i in ("0", "1", "2", "3", "4", "5", "6", "7",):
        button = waybill_questionnaire_buttons.buttons.get(button_id=i)
        button.bg_color = bg_color
        button.action_type = "reply"
        button.save()
    button = waybill_questionnaire_buttons.buttons.get(button_id="8")
    button.bg_color = non_active_button_color
    button.action_type = "none"
    button.save()
    waybill_questionnaire_buttons.save()


def get_button(vid, but_id):
    subscriber = Subscriber.objects.get(user=vid)
    questionnaire_buttons = QuestionnaireButtons.objects.get(user=subscriber)
    button = questionnaire_buttons.buttons.get(button_id=but_id)
    return button.bg_color, button.action_type, button.action_body


def get_license_button(vid, but_id):
    subscriber = Subscriber.objects.get(user=vid)
    license_questionnaire_buttons = LicensingQuestionnaireButtons.objects.get(user=subscriber)
    button = license_questionnaire_buttons.buttons.get(button_id=but_id)
    return button.bg_color, button.action_type, button.action_body


def get_waybill_button(vid, but_id):
    subscriber = Subscriber.objects.get(user=vid)
    waybill_questionnaire_buttons = WaybillQuestionnaireButtons.objects.get(user=subscriber)
    button = waybill_questionnaire_buttons.buttons.get(button_id=but_id)
    return button.bg_color, button.action_type, button.action_body


def tech_support_and_drivers_buttons(columns=6, driver_button=True):
    if driver_button:
        color = bg_color
        action_type = "reply"
    else:
        color = non_active_button_color
        action_type = "none"
    button_support = {
        "Columns": columns,
        "Rows": 1,
        "ActionBody": "info",
        "ActionType": "reply",
        "Silent": "true",
        "Text": "<font color='#FFFFFF'>Написать в техподдержку 👨‍🔧</font>",
        "BgColor": bg_color
    }
    button_for_drivers = {
        "Columns": columns,
        "Rows": 1,
        "ActionBody": "for-drivers",
        "ActionType": action_type,
        "Silent": "true",
        "Text": "<font color='#FFFFFF'>Для водителей 🚘 💳 </font>",
        "BgColor": color
    }
    button_for_license = {
        "Columns": 6,
        "Rows": 1,
        "ActionBody": "apply_for_a_taxi_permit",
        "ActionType": "reply",
        "Silent": "true",
        "Text": "<font color='#FFFFFF'>Разрешение такси 🚕 </font>",
        "BgColor": bg_color
    }
    return button_for_drivers, button_for_license, button_support


def choice_service_kb(subscriber):
    buttons = []

    if subscriber.is_driver:
        ts_button, button_for_license, drivers_button = tech_support_and_drivers_buttons()

    else:
        ts_button, button_for_license, drivers_button = tech_support_and_drivers_buttons(driver_button=False)
    buttons.append(button_for_license)
    buttons.append(ts_button)
    buttons.append(drivers_button)
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        # "CustomDefaultHeight": 60,
        "Buttons": buttons
    }
    return keyboard


def refresh_menu_rich():
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 1,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Обновить</font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6
    )


def choice_service(user):
    text = "Выберите опцию"
    subscriber = Subscriber.objects.get(user=user)
    return TextMessage(
        text=text,
        min_api_version=6,
        keyboard=choice_service_kb(subscriber)
    )


def choice_cargo_tariff():
    return TextMessage(
        text="Выберите подходящий тариф",
        min_api_version=6,
        keyboard={
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "tariff_8_cargo",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Грузовой 1,5т</font>",
                    "BgColor": bg_color
                },

                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Отменить</font>",
                    "BgColor": bg_color
                }
            ]
        }
    )


def choice_evacuator_tariff():
    return TextMessage(
        text="Выберите подходящий тариф",
        min_api_version=6,
        keyboard={
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "tariff_4_evacuator",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>До 2000 кг</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "tariff_5_evacuator",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>До 3000 кг</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "tariff_6_evacuator",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>До 3500 кг</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "tariff_7_evacuator",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>До 4000 кг</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Отменить</font>",
                    "BgColor": bg_color
                }
            ]
        },
    )


def info():
    return TextMessage(
        text="Письмо в техподдержку",
        min_api_version=6,
        tracking_data="support_letter",
        keyboard={
            "Type": "keyboard",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>В главное меню</font>",
                    "BgColor": bg_color
                }
            ]
        }
    )


def from_address(service=""):
    return TextMessage(
        text="Откуда?\nУкажите на карте или напишите в тексте в формате:\n\"Населённый пункт, название улицы, "
             "номер дома\"",
        min_api_version=6,
        tracking_data="from",
        keyboard={
            "Type": "keyboard",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "from",
                    "ActionType": "location-picker",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Указать на карте 🏁</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "/back_tariff_" + service,
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Назад</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Отменить</font>",
                    "BgColor": bg_color
                }

            ]
        }
    )


def to_address():
    return TextMessage(
        text="Куда?\nУкажите на карте или напишите в тексте в формате:\n\"Населённый пункт, название улицы, "
             "номер дома\"",
        min_api_version=6,
        tracking_data="to",
        keyboard={
            "Type": "keyboard",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "to",
                    "ActionType": "location-picker",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Указать на карте 🏁</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "/back_from",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Назад</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Отменить</font>",
                    "BgColor": bg_color
                }

            ]
        }
    )


def comment():
    return TextMessage(
        text="Для точного расчета стоимости напишите в комментарии или нажмите клавишу \"Без комментария\"",
        min_api_version=6,
        tracking_data="/comment",
        keyboard={
            "Type": "keyboard",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "/comment",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Без комментария</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "/back_to",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Назад</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Отменить</font>",
                    "BgColor": bg_color
                }

            ]
        }
    )


def get_phone():
    buttons = [
        {
            "Columns": 6,
            "Rows": 1,
            "Silent": "true",
            "ActionType": "share-phone",
            "ActionBody": "phone",
            "Text": "<font color='#FFFFFF'> 📲 Отправить</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "/back_comment",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Назад</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Отменить</font>",
            "BgColor": bg_color
        }
    ]
    keyboard = {"Type": "keyboard", "InputFieldState": "hidden", "Buttons": buttons}

    return TextMessage(text="Для отправки заказа нужен Ваш номер телефона, нажмите кнопку 📲 Отправить",
                       keyboard=keyboard, min_api_version=6)


def get_phone_for_letter():
    buttons = [
        {
            "Columns": 6,
            "Rows": 1,
            "Silent": "true",
            "ActionType": "share-phone",
            "ActionBody": "phone",
            "Text": "<font color='#FFFFFF'> 📲 Отправить</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Отменить</font>",
            "BgColor": bg_color
        }
    ]
    keyboard = {"Type": "keyboard", "InputFieldState": "hidden", "Buttons": buttons}

    return TextMessage(text="Для обращения в техподдержку нужен Ваш номер телефона, нажмите кнопку 📲 Отправить",
                       keyboard=keyboard, min_api_version=6, tracking_data="phone-number-for-support-letter")


def share_phone(name):
    buttons = [
        {
            "Columns": 6,
            "Rows": 1,
            "Silent": "true",
            "ActionType": "share-phone",
            "ActionBody": "phone",
            "Text": "<font color='#FFFFFF'>Поделиться номером телефона 📲</font>",
            "BgColor": bg_color
        }
    ]
    keyboard = {"Type": "keyboard", "InputFieldState": "hidden", "Buttons": buttons}

    return TextMessage(text="Приветствуем Вас, " + name + "!\nЧтобы подписаться - отправьте Ваш номер " + \
                            "телефона.\nНажмите на кнопку \"Поделиться номером телефона 📲\"",
                       keyboard=keyboard, min_api_version=6, tracking_data="share-phone-number")


def order_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "order",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Заказать</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "/back_comment",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отменить</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def cancel_order_or_menu_rich():
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 3,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "cancel_order",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Отменить заказ</b></font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "tel:+79581114584",
                "ActionType": "open-url",
                "OpenURLType": "external",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Позвонить</b></font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Меню</b></font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6
    )


def return_to_menu_rich():
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 2,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 2,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Меню</b></font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6
    )


def return_to_menu_or_update_rich():
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 2,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": properties.conversation_url,
                "ActionType": "open-url",
                "OpenURLType": "internal",
                "Silent": "true",
                "Text": "<font size=16 color='#ffffff'>{} {}</font>".format('🌍', 'Обновить'),
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Главное меню</b></font>",
                "BgColor": bg_color
            }

        ]
    },
        min_api_version=6
    )


def job_application_form(vid, number_button=None, text=None, order_data="", text_field="regular", answered=False):
    is_exists_buttons(vid)
    if number_button is not None:
        set_button(vid, number_button, answered)
    else:
        set_default_buttons(vid)
    keyboard = {
        "Type": "keyboard",
        "CustomDefaultHeight": 70,
        "InputFieldState": text_field,
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_0_" + get_button(vid, "0")[2],
                "ActionType": get_button(vid, "0")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Укажите свой город</font>",
                "BgColor": get_button(vid, "0")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_1_" + get_button(vid, "1")[2],
                "ActionType": get_button(vid, "1")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Фамилия Имя</font>",
                "BgColor": get_button(vid, "1")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_2_" + get_button(vid, "2")[2],
                "ActionType": get_button(vid, "2")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Номер телефона</font>",
                "BgColor": get_button(vid, "2")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_3_" + get_button(vid, "3")[2],
                "ActionType": get_button(vid, "3")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Гос. номер автомобиля</font>",
                "BgColor": get_button(vid, "3")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_4_" + get_button(vid, "4")[2],
                "ActionType": get_button(vid, "4")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Марка/модель автомобиля</font>",
                "BgColor": get_button(vid, "4")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_5_" + get_button(vid, "5")[2],
                "ActionType": get_button(vid, "5")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Количество мест</font>",
                "BgColor": get_button(vid, "5")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_6_" + get_button(vid, "6")[2],
                "ActionType": get_button(vid, "6")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Год выпуска</font>",
                "BgColor": get_button(vid, "6")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_7_" + get_button(vid, "7")[2],
                "ActionType": get_button(vid, "7")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Тип кузова, грузоподъёмность</font>",
                "BgColor": get_button(vid, "7")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "job_8_" + get_button(vid, "8")[2],
                "ActionType": get_button(vid, "8")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Цвет кузова</font>",
                "BgColor": get_button(vid, "8")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "send_application",
                "ActionType": get_button(vid, "9")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отправить заявку</font>",
                "BgColor": get_button(vid, "9")[0]
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            }
        ]
    }

    if text is None:
        return KeyboardMessage(min_api_version=6, keyboard=keyboard, tracking_data="kb-job-app-form")
    return TextMessage(text=text, min_api_version=6, keyboard=keyboard, tracking_data="job-app-form_" + order_data)


def order_buttons(driver_lat=None, driver_lon=None, radius=None):
    buttons = []
    if Order.objects.filter(ord_success=False).count() == 0:
        buttons.append(
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Заказов нет</font>",
                "BgColor": "#7360F2"
            })
    else:
        if radius is not None:
            for order in Order.objects.filter(ord_success=False):
                try:
                    loc_from = order.from_location.split("#")[1]
                except IndexError:
                    continue
                if order.tariff is None or order.service is None:
                    continue
                order_location = loc_from.split(" ")
                lat_order = order_location[0]
                lon_order = order_location[1]
                if is_appropriate_address(float(driver_lat), float(driver_lon), float(lat_order), float(lon_order),
                                          float(radius)):
                    buttons.append(
                        {
                            "Columns": 3,
                            "Rows": 1,
                            "ActionBody": "driver|" + order.order_id,
                            "ActionType": "reply",
                            "Silent": "true",
                            "Text": "<font color='#FFFFFF'>{0}</font>".format(order.from_location.split("#")[0]),
                            "BgColor": "#7360F2"
                        })
            if len(buttons) == 0:
                buttons.append(
                    {
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": "menu",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>Заказов нет</font>",
                        "BgColor": "#7360F2"
                    })
        else:
            for order in Order.objects.filter(ord_success=False):
                try:
                    order.from_location.split("#")[1]
                except IndexError:
                    continue
                if order.tariff == "" or order.service == "":
                    continue
                buttons.append(
                    {
                        "Columns": 3,
                        "Rows": 1,
                        "ActionBody": "driver|" + order.order_id,
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>{0}</font>".format(order.from_location.split("#")[0]),
                        "BgColor": "#7360F2"
                    })

    return buttons


def broadcast_source(buttons: list):
    i = -300
    j = -1
    number = Subscriber.objects.count()
    customers = Subscriber.objects.all()
    while j < number:
        i += 300
        j += 300

        recipient = list(customers[i:j].values_list("user", flat=True))
        bcast = dict(broadcast_list=recipient)
        mess = dict(bcast,
                    min_api_version=6,
                    sender=dict(name="ЗАКАЗЫ"),
                    tracking_data="tow",
                    keyboard=dict(Type="keyboard", InputFieldState="hidden", Buttons=buttons))
        requests.post(cast, json.dumps(mess), headers=headers)


def take_order_or_not_rich(order_id):
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 2,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "take-order|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Взять заказ</b></font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>В меню</b></font>",
                "BgColor": bg_color
            }

        ]
    },
        min_api_version=6
    )


def driver_arrival_interval(order_owner_user, order_id):
    buttons = []
    for i in (5, 10, 15, 20, 25, 30, 40, 50, 60):
        buttons.append({
            "Columns": 2,
            "Rows": 1,
            "ActionBody": "time-interval|" + str(i) + "|" + order_owner_user + "|" + order_id,
            "ActionType": "reply",
            "Text": f"<font color='#FFFFFF'>{i} мин</font>",
            "BgColor": bg_color
        })
    keyboard = {"Type": "keyboard", "InputFieldState": "hidden", "Buttons": buttons}
    return keyboard


def accept_the_order_or_cancel_kb(order_id):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "order-cancellation|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отменить</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "accept-order|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Принять заказ</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def to_menu_rich():
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 1,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>В меню</b></font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6
    )


def to_menu_and_permission_taxi_kb(vid):
    buttons = [
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>В меню</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "permission-taxi",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Разрешение такси</font>",
            "BgColor": bg_color
        }
    ]
    subscriber = Subscriber.objects.get(user=vid)
    wbe = WaybillEntry.objects.get(applicant=subscriber)
    if not wbe.closed:
        buttons.append(
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "close-waybill",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Закрыть путевой лист</font>",
                "BgColor": bg_color
            }
        )

    return KeyboardMessage(keyboard={
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": buttons
    },
        min_api_version=6
    )


def to_menu_kb(text=None):
    return TextMessage(text=text, keyboard={
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }
        ]
    }, min_api_version=6)


def cancel_kb(tracking_data):
    return KeyboardMessage(keyboard={
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": f"<font color='#FFFFFF'>Отмена</font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6,
        tracking_data=tracking_data
    )


def back_kb(to, tracking_data, label="Отмена"):
    return KeyboardMessage(keyboard={
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": to,
                "ActionType": "reply",
                "Silent": "true",
                "Text": f"<font color='#FFFFFF'>{label}</font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6,
        tracking_data=tracking_data
    )


def after_take_driver_kb(order_id):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "call-to-client|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Позвониь клиенту</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "arrived-at-place|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Прибыл на место заказа</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "order-cancellation|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отказаться от заказа</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def after_accept_arrival_kb(order_id):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "in-arrival-call-to-client|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Позвониь клиенту</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "landing|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Посадка</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "order-cancellation|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отказаться от заказа</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def call_or_cancel_kb(order_id):
    order = Order.objects.get(order_id=order_id)
    user = order.owner.user
    phone = Subscriber.objects.get(user=user).phone
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "accept-order|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отмена</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "tel:" + phone,
                "ActionType": "open-url",
                "OpenURLType": "external",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Да</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def call_or_cancel_in_arrival_moment_kb(order_id):
    order = Order.objects.get(order_id=order_id)
    user = order.owner.user
    phone = Subscriber.objects.get(user=user).phone
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "accept-arrival|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отмена</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "tel:" + phone,
                "ActionType": "open-url",
                "OpenURLType": "external",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Да</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def arrival_or_cancel_kb(order_id):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "accept-order|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отмена</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "accept-arrival|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Да</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def start_trip_or_cancel_kb(order_id):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "accept-arrival|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отмена</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "start_trip|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Да</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def finish_trip_kb(order_id):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "finish_trip|" + order_id,
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Приехали</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def main_menu_kb(vid, blocked_item=''):
    if blocked_item == "block_waybill":
        active_type = "none"
        color = non_active_button_color
    else:
        active_type = "reply"
        color = bg_color
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        # "CustomDefaultHeight": 40,
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "personal-account",
                "ActionType": active_type,
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Личный кабинет</font>",
                "BgColor": color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "payment-for-car",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Оплата за разрешение такси \"Маруся\" 💳</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "set-odometer",
                "ActionType": active_type,
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Путевой лист</font>",
                "BgColor": color
            }
        ]
    }
    return keyboard


def to_orders(order_id):
    return [
        {
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "take-order|" + str(order_id),
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Взять заказ</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "get-all-orders",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Показать все заказы</font>",
            "BgColor": bg_color
        }
    ]


def show_less_remote_locations_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "get-all-orders",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Показать все заказы</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "get-distance-limited-orders",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Показать ближайшие заказы</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def driver_location_kb(radius_distance):
    return TextMessage(
        text="Укажите своё местоположение",
        tracking_data="radius_distance|" + radius_distance,
        min_api_version=6,
        keyboard={
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": [
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "reply",
                    "ActionType": "location-picker",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Указать на карте 🏁</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "get-distance-limited-orders",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Назад</font>",
                    "BgColor": bg_color
                },
                {
                    "Columns": 3,
                    "Rows": 1,
                    "ActionBody": "menu",
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>Отменить</font>",
                    "BgColor": bg_color
                }
            ]
        })


def balance_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "set-balance",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Пополнить баланс</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "for-drivers",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def license_form(vid, number_button=None, text=None, order_data="", text_field="regular", answered=False, data=""):
    is_exists_licensing_buttons(vid)
    if number_button is not None:
        set_license_button(vid, number_button, answered)
    else:
        set_default_license_buttons(vid)
    keyboard = {
        "Type": "keyboard",
        "CustomDefaultHeight": 60,
        "InputFieldState": text_field,
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_0_" + get_license_button(vid, "0")[2],
                "ActionType": get_license_button(vid, "0")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Имя</font>",
                "BgColor": get_license_button(vid, "0")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_1_" + get_license_button(vid, "1")[2],
                "ActionType": get_license_button(vid, "1")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Фамилия</font>",
                "BgColor": get_license_button(vid, "1")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_2_" + get_license_button(vid, "2")[2],
                "ActionType": get_license_button(vid, "2")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Номер телефона</font>",
                "BgColor": get_license_button(vid, "2")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_3_" + get_license_button(vid, "3")[2],
                "ActionType": get_license_button(vid, "3")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Гос. номер автомобиля</font>",
                "BgColor": get_license_button(vid, "3")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_4_" + get_license_button(vid, "4")[2],
                "ActionType": get_license_button(vid, "4")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Марка автомобиля</font>",
                "BgColor": get_license_button(vid, "4")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_5_" + get_license_button(vid, "5")[2],
                "ActionType": get_license_button(vid, "5")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Модель автомобиля</font>",
                "BgColor": get_license_button(vid, "5")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_6_Отправьте фото первой развёрнутой страницы паспорта",
                "ActionType": get_license_button(vid, "6")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отправить фото паспорта (первая страница)</font>",
                "BgColor": get_license_button(vid, "6")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_7_Отправьте фото паспорта (прописка)",
                "ActionType": get_license_button(vid, "7")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отправить фото паспорта (прописка)</font>",
                "BgColor": get_license_button(vid, "7")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_8_Отправьте фото лицевой стороны СТС",
                "ActionType": get_license_button(vid, "8")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отправить фото лицевой стороны СТС</font>",
                "BgColor": get_license_button(vid, "8")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "license_9_Отправьте фото задней стороны СТС",
                "ActionType": get_license_button(vid, "9")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отправить фото задней стороны СТС</font>",
                "BgColor": get_license_button(vid, "9")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "apply_for_a_taxi_permit",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "send_licensing_application",
                "ActionType": get_license_button(vid, "10")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отправить заявку</font>",
                "BgColor": get_license_button(vid, "10")[0]
            }
        ]
    }

    if text is None:
        return KeyboardMessage(min_api_version=6, keyboard=keyboard, tracking_data="kb-license-app-form")
    return TextMessage(text=text, min_api_version=6, keyboard=keyboard, tracking_data="license-app-form_" + order_data)


def choice_region_kb():
    region_buttons = []
    for condition_for_region in ConditionsForRegions.objects.all():
        region_buttons.append(
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": str(condition_for_region.region_name),
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>" + str(condition_for_region.region_name) + "</font>",
                "BgColor": bg_color
            })

    region_buttons.append(
        {
            "Columns": 6,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Назад</font>",
            "BgColor": bg_color
        }
    )

    keyboard = {
        "Type": "keyboard",
        "CustomDefaultHeight": 60,
        "InputFieldState": "hidden",
        "Buttons": region_buttons
    }
    return KeyboardMessage(min_api_version=6, keyboard=keyboard)


def send_request_or_come_back():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "license_form",
                "ActionType": "",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Подать заявку на оформление разрешения такси</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "apply_for_a_taxi_permit",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#ffffff'>Назад</font>",
                "BgColor": bg_color
            }
        ]
    }
    return KeyboardMessage(min_api_version=6, keyboard=keyboard)


def waybill_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "for-drivers",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            }
        ]
    }
    return KeyboardMessage(min_api_version=6, keyboard=keyboard)


def waybill_form(vid, number_button=None, text=None, order_data="", text_field="regular", answered=False, data=""):
    if WaybillQuestionnaireButtons.objects.get(user=Subscriber.objects.get(user=vid)).edit:
        action_body = "waybill_6_Введите номер СНИЛС"
        button_label = "СНИЛС"
    else:
        action_body = "waybill_6_" + get_waybill_button(vid, "6")[2]
        button_label = "Показание одометра"

    is_exists_waybill_buttons(vid)

    if number_button is not None:
        if data == "retry":
            order_data = number_button
        else:
            set_waybill_button(vid, number_button, answered)
    else:
        set_default_waybill_buttons(vid)
    keyboard = {
        "Type": "keyboard",
        "CustomDefaultHeight": 65,
        "InputFieldState": text_field,
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "waybill_0_" + get_waybill_button(vid, "0")[2],
                "ActionType": get_waybill_button(vid, "0")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Фамилия</font>",
                "BgColor": get_waybill_button(vid, "0")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "waybill_1_" + get_waybill_button(vid, "1")[2],
                "ActionType": get_waybill_button(vid, "1")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Имя</font>",
                "BgColor": get_waybill_button(vid, "1")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "waybill_2_" + get_waybill_button(vid, "2")[2],
                "ActionType": get_waybill_button(vid, "2")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отчество</font>",
                "BgColor": get_waybill_button(vid, "2")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "waybill_3_" + get_waybill_button(vid, "3")[2],
                "ActionType": get_waybill_button(vid, "3")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Серия удостоверения</font>",
                "BgColor": get_waybill_button(vid, "3")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "waybill_4_" + get_waybill_button(vid, "4")[2],
                "ActionType": get_waybill_button(vid, "4")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Номер удостоверения</font>",
                "BgColor": get_waybill_button(vid, "4")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "wb_car_choice",
                "ActionType": get_waybill_button(vid, "5")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Выбор ТС</font>",
                "BgColor": get_waybill_button(vid, "5")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": f"{action_body}",
                "ActionType": get_waybill_button(vid, "6")[1],
                "Silent": "true",
                "Text": f"<font color='#FFFFFF'>{button_label}</font>",
                "BgColor": get_waybill_button(vid, "6")[0]
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "waybill_7_" + get_waybill_button(vid, "7")[2],
                "ActionType": get_waybill_button(vid, "7")[1],
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Установка времени</font>",
                "BgColor": get_waybill_button(vid, "7")[0]
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "verify-data",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Сохранить</font>",  # todo new
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "to-menu-from-registered-form",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }
        ]
    }

    if text is None:
        return KeyboardMessage(min_api_version=6, keyboard=keyboard,
                               tracking_data=f"kb-waybill-app-form_"+str(number_button))
    return TextMessage(text=text, min_api_version=6, keyboard=keyboard, tracking_data=f"waybill-app-form_{order_data}")


def download_waybill_or_edit_kb(text=''):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "set-odometer",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Скачать путёвку</b></font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "user-registration",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Редактировать данные для путёвки</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "for-drivers",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#ffffff'>Назад</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#ffffff'>В главное меню</font>",
                "BgColor": bg_color
            }
        ]
    }
    if text == '':
        return KeyboardMessage(min_api_version=6, keyboard=keyboard)
    else:
        return TextMessage(text=text, min_api_version=6, keyboard=keyboard)


def set_value_odometer():
    keyboard = {
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "save_odometer_value",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Сохранить показания одометра</b></font>",
                "BgColor": bg_color
            }
        ]
    }
    return TextMessage(text="Введите показание одометра", min_api_version=6, keyboard=keyboard,
                       tracking_data="save_odometer_value")


def download_waybill(url):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": url,
                "ActionType": "open-url",
                "OpenURLType": "external",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>Скачать</b></font>",
                "BgColor": bg_color
            }
        ]
    }
    return TextMessage(text="Путёвка успешно сформирована, чтобы её получить - нажмите кнопку \"Скачать\"",
                       min_api_version=6, keyboard=keyboard)


def payment_for_services():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'><b>В меню</b></font>",
                "BgColor": bg_color
            }
        ]
    }
    return TextMessage(text="Благодарим за оплату! После подтверждения оплаты администратором ваш аккаунт будет "
                            "разблокирован и работа бота возобновится!",
                       min_api_version=6, keyboard=keyboard)


def personal_account_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "CustomDefaultHeight": 50,
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "my-cars",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Мои автомобили</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "choice-car",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Выбрать автомобиль</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "permission-taxi",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Разрешение такси</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "user-registration",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Редактировать личные данные</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }
        ]
    }
    return KeyboardMessage(min_api_version=6, keyboard=keyboard)


def my_cars(vid, text='', payments=False):
    s = Subscriber.objects.get(user=vid)
    if payments:
        buttons = [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }]
    else:
        buttons = [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "personal-account",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Назад</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }
        ]
    my_cars_filter = Car.objects.filter(car_owner=s)
    if my_cars_filter.exists():
        my_cars_list = list(my_cars_filter.all())
        my_cars_list.sort(key=sort_by_car)
        for car in my_cars_list:
            if payments:
                buttons.append(
                    {
                        "Columns": 4,
                        "Rows": 1,
                        "ActionBody": "reply",
                        "ActionType": "none",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>" + str(car.car_brand) + " " + str(car.car_model) + " " + str(
                            car.car_number) + "</font>",
                        "BgColor": bg_color
                    })
                buttons.append(
                    {
                        "Columns": 2,
                        "Rows": 1,
                        "ActionBody": str(car.link_for_payment),
                        "ActionType": 'open-url',
                        "OpenURLType": 'external',
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>Оплатить 💰</font>",
                        "BgColor": bg_color
                    })
            else:
                buttons.append(
                    {
                        "Columns": 5,
                        "Rows": 1,
                        "ActionBody": f"set-vin-for-my-car_{car.car_number}",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>" + str(car.car_brand) + " " + str(car.car_model) + " " + str(
                            car.car_number) + "</font>",
                        "BgColor": bg_color
                    })
                buttons.append(
                    {
                        "Columns": 1,
                        "Rows": 1,
                        "ActionBody": "del-car_" + str(car.car_number),
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#ff0000'>❌</font>",
                        "BgColor": bg_color
                    }
                )
    else:
        buttons.append(
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "choice-car",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Выбрать автомобиль</font>",
                "BgColor": bg_color
            }
        )
        keyboard = {
            "Type": "keyboard",
            "InputFieldState": "hidden",
            "Buttons": buttons
        }
        return TextMessage(text=text + "\n\nВ вашем списке нет автомобилей, хотите выбрать автомобиль?",
                           min_api_version=6, keyboard=keyboard)

    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": buttons
    }

    default_text = "*Ваш список автомобилей*\nДля просмотра и изменения VIN-кода (или номера кузова) " \
                   "нажмите на кнопку с названием автомобиля.\n\n" \
                   "Для удаления автомобиля из вашего списка нажмите на кнопку ❌"
    if text == '':
        text = default_text
    else:
        text += "\n\n" + default_text

    return TextMessage(text=text, min_api_version=6, keyboard=keyboard)


def choice_from_my_cars(vid, action=None, next_to=None, act="in-form-create-car"):
    s = Subscriber.objects.get(user=vid)
    is_exists_waybill_buttons(vid)

    if next_to == 'to-waybill-form':
        back_to = "user-registration"
    else:
        back_to = "set-odometer"

    buttons = [
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": back_to,
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Назад</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>В главное меню</font>",
            "BgColor": bg_color
        }
    ]
    my_cars_filter = Car.objects.filter(car_owner=s)
    count = my_cars_filter.count()
    if count > 0:
        if count == 1:
            if next_to == 'to-waybill-form':
                return list_of_cars(vid, text='', common_list='True', next_to=next_to)
            else:
                car = my_cars_filter.get()
                from botviber.handler import quick_create_waybill
                
                car_str = car.car_brand + ' ' + car.car_model + ' ' + car.car_number
                if not car.is_available:
                    return [to_menu_kb("Автомобиль " + car_str +
                                       " заблокирован, вам отказано в получении "
                                       "путевого листа!")]
                if not car.is_active_license:
                    return [to_menu_kb("Лицензия автомобиля " + car_str +
                                                           " аннулирована, вам отказано в получении "
                                                           "путевого листа!")]

                return quick_create_waybill(vid, car)

        else:
            if my_cars_filter.exists():
                for car in my_cars_filter.all():
                    if action is None:
                        action_body = "choice-car_" + str(car.car_number) + "_" + next_to
                    else:
                        action_body = action + "_" + str(car.car_number) + "_" + next_to

                    buttons.append({
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": action_body,
                        "ActionType": 'reply',
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>" + str(car.car_brand) + " " + str(
                            car.car_model) + " " + str(
                            car.car_number) + "</font>",

                        "BgColor": bg_color
                    })
            keyboard = {
                "Type": "keyboard",
                "InputFieldState": "hidden",
                "Buttons": buttons
            }
            if action is None:
                return [TextMessage(text="Выберите автомобиль", min_api_version=6),
                        KeyboardMessage(min_api_version=6, keyboard=keyboard)]
            else:
                return [TextMessage(text="Выберите автомобиль", min_api_version=6),
                        KeyboardMessage(min_api_version=6, keyboard=keyboard, tracking_data="save-odometer-value")]

    else:
        return list_of_cars(vid, text='', common_list='True', next_to=next_to)


def list_of_cars(vid, text='', button_color_and_actions=None, index=0, found_cars=None, common_list='False',
                 next_to=None):
    if common_list == 'True':
        back_to = "user-registration"
        next_to = "to-waybill-form" if next_to is None else next_to
    else:
        back_to = "personal-account"
        next_to = "common_list_of_cars" if next_to is None else next_to

    step = 22
    if button_color_and_actions is None:
        button_color_and_actions = {}
    s = Subscriber.objects.get(user=vid)
    description = ''
    my_cars_filter = Car.objects.filter(car_owner=s)

    choiced_cars = []
    if my_cars_filter.exists():
        for car in my_cars_filter.all():
            choiced_cars.append(car.car_number)

    if int(index) > 0:
        set_all_cars = set(Car.objects.all())
        set_my_cars = set(my_cars_filter)
        set_all_cars.difference(set_my_cars)
        all_cars = list(set_all_cars)

    elif found_cars is not None:
        all_cars = found_cars
    else:
        all_cars = list(Car.objects.all())
    count = len(all_cars)
    all_cars.sort(key=sort_by_car)
    buttons = [
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": back_to,
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>Назад</font>",
            "BgColor": bg_color
        },
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>В главное меню</font>",
            "BgColor": bg_color
        }
    ]

    if count <= step:
        for car in all_cars:
            buttons = car_buttons(button_color_and_actions, buttons, index, car, choiced_cars, description, common_list,
                                  next_to)
    if count > step:
        index = int(index)
        end_index = index + step
        i = index
        for car in all_cars[index:end_index]:
            if i == count:
                end_index = 0
                break
            i += 1
            buttons = car_buttons(button_color_and_actions, buttons, index, car, choiced_cars, description, common_list,
                                  next_to)
        previous_next_buttons(buttons, count, end_index, index, step, "long-list-cars", common_list, next_to)

    keyboard = {
        "Type": "keyboard",
        "Buttons": buttons
    }

    return TextMessage(text=text + "\n\nДля добавления автомобиля в свой список введите в поиске его гос. номер или "
                                   "выберите его из общего списка!", min_api_version=6,
                       keyboard=keyboard, tracking_data='car-search-by-number_' + str(common_list) + '_' + next_to)


def car_buttons(button_color_and_actions, buttons, index, car, choiced_cars, description, common_list, next_to):
    if common_list == 'True':
        action = "car-choice-and-add-my-list_" + str(car.car_number) + "_" + str(next_to)
    else:
        action = "add-car_" + str(car.car_number) + "_" + str(index)
    buttons.append(
        {
            "Columns": 6,
            "Rows": 1,
            "ActionBody": action,
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>" + str(car.car_brand) + " " + str(car.car_model) + " " + str(
                car.car_number) + "</font>",
            "BgColor": bg_color
        })
    return buttons


def permission_for_cars_buttons(list_of_my_cars):
    buttons = [{
        "Columns": 3,
        "Rows": 1,
        "ActionBody": "personal-account",
        "ActionType": "reply",
        "Silent": "true",
        "Text": "<font color='#FFFFFF'>Назад</font>",
        "BgColor": bg_color
    },
        {
            "Columns": 3,
            "Rows": 1,
            "ActionBody": "menu",
            "ActionType": "reply",
            "Silent": "true",
            "Text": "<font color='#FFFFFF'>В главное меню</font>",
            "BgColor": bg_color
        }]

    for car in list_of_my_cars:
        if isinstance(car, tuple):
            text_1 = car[0]
            car_ = car[1]
            text_2 = car[2]
            buttons.append(
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "reply",
                    "ActionType": "none",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>" + text_1 + car_.car_brand + ' ' + car_.car_model + ' ' + car_.car_number + text_2 + "</font>",
                    "BgColor": bg_color
                })
        else:
            buttons.append(
                {
                    "Columns": 6,
                    "Rows": 1,
                    "ActionBody": "permission_" + car.car_number,
                    "ActionType": "reply",
                    "Silent": "true",
                    "Text": "<font color='#FFFFFF'>" + car.car_brand + ' ' + car.car_model + ' ' + car.car_number + "</font>",
                    "BgColor": bg_color
                })

    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": buttons
    }

    return TextMessage(text='Выберите автомобиль для которого хотите получить разрешение',
                       keyboard=keyboard,
                       min_api_version=6)


def previous_next_buttons(*args):
    buttons, count, end_index, index, step, buttons_holder, common_list, next_to = args[0], args[1], args[2], args[3], \
                                                                                   args[4], args[5], args[6], args[7]
    count = args[1]
    command_next = ''
    command_previous = ''
    if buttons_holder == "long-list-cars":
        command_next = "/next-cars" + "_" + str(args[2]) + "_" + common_list + "_" + next_to
        command_previous = "/prev-cars" + "_" + str(args[3]) + "_" + common_list + "_" + next_to

    if count > end_index and index < step:
        buttons.append(
            {'Columns': 6, 'Rows': 1, 'ActionBody': command_next, 'ActionType': 'reply',
             'Text': "<font color='#ffffff'><b>{}</b></font>".format('Далее >>'),
             'TextHAlign': "center", 'TextVAlign': "center", 'TextSize': "small", 'BgColor': bg_color,
             'Silent': 'true'
             }
        )
    elif count > end_index and index >= step:
        buttons.append(
            {'Columns': 3, 'Rows': 1, 'ActionBody': command_previous, 'ActionType': 'reply',
             'Text': "<font color='#ffffff'><b>{}</b></font>".format('<< Назад'),
             'TextHAlign': "center", 'TextVAlign': "center", 'TextSize': "small", 'BgColor': bg_color,
             'Silent': 'true'
             }
        )
        buttons.append(
            {'Columns': 3, 'Rows': 1, 'ActionBody': command_next, 'ActionType': 'reply',
             'Text': "<font color='#ffffff'><b>{}</b></font>".format('Далее >>'),
             'TextHAlign': "center", 'TextVAlign': "center", 'TextSize': "small", 'BgColor': bg_color,
             'Silent': 'true'
             }
        )

    elif count <= end_index:
        buttons.append(
            {'Columns': 6, 'Rows': 1, 'ActionBody': command_previous, 'ActionType': 'reply',
             'Text': "<font color='#ffffff'><b>{}</b></font>".format('<< Назад'),
             'TextHAlign': "center", 'TextVAlign': "center", 'TextSize': "small", 'BgColor': bg_color,
             'Silent': 'true'
             }
        )


def close_waybill_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "close-waybill",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Закрыть путевой лист</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def confirm_or_correct_kb():
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Подтвердить</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 3,
                "Rows": 1,
                "ActionBody": "user-registration",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Исправить</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def notify_for_entering_data_rich():
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 1,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "set-snils",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Добавьте СНИЛС</font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6
    )


def enter_later_kb():
    keyboard = {
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Ввести позже</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def entering_vin_kb(car_number, odometer_value):
    keyboard = {
        "Type": "keyboard",
        "InputFieldState": "hidden",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": f"vin-retry_{car_number}_{odometer_value}",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Ввести VIN-код</font>",
                "BgColor": bg_color
            },
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Отмена</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def notify_for_entering_vin_rich(car_number, odometer_value):
    return TextMessage(text=f"Введите VIN-код автомобиля c госномером {car_number}, "
                            "его можно посмотреть как на самом автомобиле, так и в СТС",
                       tracking_data=f'vin-code_{car_number}_{odometer_value}',
                       min_api_version=6)


def entering_vin_code_for_car_in_my_list(car, vin_code):
    default_text = f"Введите VIN-код автомобиля {car}, " \
                   f"его можно посмотреть как на самом автомобиле, так и в СТС"
    if vin_code == '':
        text = default_text
    else:
        text = default_text + "\n\nРанее введённый VIN-код:\n" \
                              f"{vin_code}\n\nПри обнаружении ошибки введите его заново. " \
                              f"Используются только цифры и символы латинского алфавита, за " \
                              f"исключением 'I', 'O' и 'Q'."
    return TextMessage(text=text, tracking_data=f'set-vin-code_{car.car_number}', min_api_version=6)


def confirm_diagnostic_card_rich(vid, text, car):
    return [TextMessage(text=text, min_api_version=6),
            RichMediaMessage(rich_media={
                "ButtonsGroupColumns": 6,
                "ButtonsGroupRows": 3,
                "BgColor": "#FFFFFF",
                "Buttons": [
                    {
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": f"confirm-ti_{car.car_number}",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>Подтвердить техосмотр</font>",
                        "BgColor": bg_color
                    },
                    {
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": f"edit-vin-for-my-car_{car.car_number}",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>Просмотр и изменение VIN</font>",
                        "BgColor": bg_color
                    },
                    {
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": "menu",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>В меню</font>",
                        "BgColor": bg_color
                    },

                ]
            },
                min_api_version=6,
                keyboard=main_menu_kb(vid)
            )]


def edit_vin_rich(vid, text, car):
    return [TextMessage(text=text, min_api_version=6),
            RichMediaMessage(rich_media={
                "ButtonsGroupColumns": 6,
                "ButtonsGroupRows": 1,
                "BgColor": "#FFFFFF",
                "Buttons": [
                    {
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": f"edit-vin-for-my-car_{car.car_number}",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>Просмотр и изменение VIN</font>",
                        "BgColor": bg_color
                    },
                ]
            },
                min_api_version=6,
                keyboard=main_menu_kb(vid)
            )]


def return_to_entering_data(vid):
    return RichMediaMessage(rich_media={
                "ButtonsGroupColumns": 6,
                "ButtonsGroupRows": 1,
                "BgColor": "#FFFFFF",
                "Buttons": [
                    {
                        "Columns": 6,
                        "Rows": 1,
                        "ActionBody": "user-registration",
                        "ActionType": "reply",
                        "Silent": "true",
                        "Text": "<font color='#FFFFFF'>Редактировать данные</font>",
                        "BgColor": bg_color
                    }
                ]
            },
                min_api_version=6,
                keyboard=main_menu_kb(vid)
            )


def to_main_kb():
    keyboard = {
        "Type": "keyboard",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": "menu",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>В меню</font>",
                "BgColor": bg_color
            }
        ]
    }
    return keyboard


def where_get_pts(tracking_data):
    return RichMediaMessage(rich_media={
        "ButtonsGroupColumns": 6,
        "ButtonsGroupRows": 1,
        "BgColor": "#FFFFFF",
        "Buttons": [
            {
                "Columns": 6,
                "Rows": 1,
                "ActionBody": f"pts-info_{tracking_data}",
                "ActionType": "reply",
                "Silent": "true",
                "Text": "<font color='#FFFFFF'>Где взять номер ПТС?</font>",
                "BgColor": bg_color
            }
        ]
    },
        min_api_version=6
    )
