import json
import socket
import hashlib
from time import sleep
from urllib.parse import unquote
import math
from math import sin, cos, asin, sqrt

host = 'domen.site.ru'
port = 33090
operator_login = 'r.f.login'
operator_password = 'passssss'


def distance(unit_id, tariff_id, lat_from, lon_from, lat_to, lon_to):
    sock = socket.socket()
    sock.connect((host, port))
    sock.sendall(b'1 hello\n')
    while True:
        data = sock.recv(1024)
        if not data:
            break
        s = data.split(b' ')
        if len(s) < 2:
            break
        mesg = b''
        count = 0
        for v in s:
            if count > 0:
                mesg += v + b' '
            count += 1
        mesg = mesg.strip()
        if mesg == b'who are you?':
            sock.sendall(b'2 api ' + operator_login.encode() + b'\n')
        elif mesg == b'password for ' + operator_login.encode():
            sock.sendall(b'3 password ' + hashlib.md5(operator_password.encode()).hexdigest().encode() + b'\n')
        elif s[1] == b'hello' and s[2] == operator_login.encode():
            sock.sendall(b'4 get_distance ' +
                         b'with_bank_card=0' +
                         b'&tarif_id=' + tariff_id.encode() +
                         b'&to[]=.&to[]=.&'
                         b'unit_id=' + unit_id.encode() +
                         b'&lat[]=' + lat_from.encode() + b'&lon[]=' + lon_from.encode() +
                         b'&lat[]=' + lat_to.encode() + b'&lon[]=' + lon_to.encode() + b'\n')
        elif s[1] == b'distance':
            try:
                son = unquote(s[2].decode())
                return json.loads(son[:son.index('nodes') - 3] + "}")
            except json.decoder.JSONDecodeError:
                pass

    sock.close()


def get_geo_distance(lat1, lon1, lat2, lon2):
    earth_radius_km = 6372.795
    lat1r = lat1 * math.pi / 180
    lon1r = lon1 * math.pi / 180
    lat2r = lat2 * math.pi / 180
    lon2r = lon2 * math.pi / 180
    u = sin((lat2r - lat1r)/2)
    v = sin((lon2r - lon1r)/2)
    return 2 * earth_radius_km * asin(sqrt(u * u + cos(lat1r) * cos(lat2r) * v * v))


def is_appropriate_address(lat1, lon1, lat2, lon2, radius):
    return get_geo_distance(lat1, lon1, lat2, lon2) < radius
