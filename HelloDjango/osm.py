import json

import requests


def get_address(lat, lon):
    r = requests.get('https://nominatim.openstreetmap.org/reverse?lat='+str(lat)+'&lon='+str(lon)+'&format=json')
    try:
        address = json.loads(r.text)['address']
        city = address['city']
        street = address['road']
        if str(street).startswith('улица'):
            street = str(street).replace('улица', '') + ' улица'
        elif str(street).startswith('проспект'):
            street = str(street).replace('проспект', '') + ' проспект'
        house = address['house_number']
        address_str = city + ', ' + street + ', ' + house
        return address_str + "#" + str(lat) + " " + str(lon)
    except KeyError:
        return json.loads(r.text)['display_name'] + "#" + str(lat) + " " + str(lon)

### address format
# country city street
# street=<housenumber> <streetname>
# city=<city>
# county=<county>
# state=<state>
# country=<country
# ###


def coordinates_from_address(address):
    city = str(address.split(",")[0]).strip()
    street = str(address.split(",")[1]).strip()
    try:
        house = str(address.split(",")[2]).strip()
        s = house + " " + street
    except IndexError:
        s = street

    r = requests.get('https://nominatim.openstreetmap.org/search?'
                     # 'country=' + country
                     + '&city=' + city + '&street='
                     + s + '&format=json')  # номер дома ещё нужно добавить
    return str(json.loads(r.text)[0]['lat']) + " " + str(json.loads(r.text)[0]['lon'])