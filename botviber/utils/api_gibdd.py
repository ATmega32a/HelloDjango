import json
import re
from datetime import datetime
import requests
from HelloDjango.exceptions import MissingKeyException, BadRequestException, DCardNotFoundException

token = "92a2ebe08b53ceb723d0c7caa7293f14"


def vin_validation(num: str) -> tuple[str, str]:
    num = num.strip().upper()

    # num_len = len(num)
    # if num_len != 17:
    #     return '', f"Вы ввели {num_len} знаков\nДлина VIN должна быть 17 знаков, без пробелов и тире. "\
    #                 f"В VIN разрешено использовать только следующие символы латинского языка и арабские цифры: "\
    #                 f"0 1 2 3 4 5 6 7 8 9 A B C D E F G H J K L M N P R S T U V W X Y Z. Использовать буквы I O Q "\
    #                 f"запрещено. Введите корректный VIN"
    #
    # pattern = r"^[A-HJ-NPR-Z0-9]{17}$"
    # if not re.match(pattern, num):
    #     return '', f'VIN-код должен содержать только буквенно-цифровые символы, за исключением "I", "O" и "Q"'

    return num, ''

def pts_series_number_validation(num: str) -> tuple[str, str]:
    # тут код для приведения серии и номера ПТС к стандартному виду
    num.replace(" ", "")
    return num, ''

def get_diagnostic_card(vin):
    url = f"https://api-cloud.ru/api/gibdd.php?vin={vin}&type=eaisto&token={token}"
    response = requests.get(url)
    return response.text


def check_dc(vin: str):
    data = get_diagnostic_card(vin)
    r = json.loads(data)
    try:
        if r["status"] == 200:
            if r['count'] != 0:
                return r["records"][0]["dcExpirationDate"]
            else:
                raise DCardNotFoundException()
        else:
            raise BadRequestException()

    except KeyError:
        raise MissingKeyException()


def check_dc_exp_date(dc_expiration_date: datetime.date) -> bool:
    if dc_expiration_date >= datetime.now().date():
        return True
    return False

def get_vin_details(vin):
    url = f"https://api-cloud.ru/api/gibdd.php?vin={vin}&type=gibdd&token={token}"
    response = requests.get(url)
    return response.text

def get_series_number_pts_by_vin(vin):
    data = get_vin_details(vin)
    r = json.loads(data)
    return r['vehiclePassport']['number']

def car_number_to_vin_converter(car_number):
    url = f"https://api-cloud.ru/api/converter.php?type=search&string={car_number}&token={token}"
    response = requests.get(url)
    return response.text


def get_info_by_car_number(car_number):
    data = car_number_to_vin_converter(car_number)
    try:
        vin_ = json.loads(data)['partner']['result']['vin']
        year_ = json.loads(data)['partner']['result']['year']
        if vin_ is not None:
            return vin_, year_
        else:
            body_ = json.loads(data)['partner']['result']['body']
            return body_, year_

    except Exception:
        pass
