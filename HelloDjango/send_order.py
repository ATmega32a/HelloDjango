import socket
import hashlib
import urllib.parse

host = 'domen.site.ru'
port = 33090
operator_login = 'r.f.login'
operator_password = 'passssss'


def send_order(unit_id='', tariff_id='', phone='', addr_from='', addr_to='', comment=''):
    sock = socket.socket()
    sock.connect((host, port))
    sock.sendall(b'1 hello\n')
    while True:
        data = sock.recv(1000000).strip()
        if data == "":
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
            sock.sendall(b'4 add_order unit_id=' + unit_id.encode() + b'&tarif_id=' + tariff_id.encode() +
                         b'&call_from=' + urllib.parse.quote_plus(phone).encode() + b'&to[]='
                         + urllib.parse.quote(addr_from).encode() + b'&to[]=' + urllib.parse.quote(addr_to).encode()
                         + b'&comment=' + urllib.parse.quote(comment).encode() + b'&distribution_method=1\n')
        elif s[1] == b'new_order':
            breaking = False
            params = s[3].split(b'&')
            for v in params:
                param = v.split(b'=')
                if param[0] == b'call_from':
                    phone2 = urllib.parse.unquote(param[1].decode('UTF-8'))
                    if phone == phone2:
                        breaking = True
                        break
            if breaking:
                break
        elif s[1] == b'err_msg':
            break
    sock.close()
    return data
