import socket
import hashlib

host = 'domen.site.ru'
port = 33090
operator_login = 'r.f.login'
operator_password = 'passssss'


def cancel(order_id):
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
            sock.sendall(b'4 cancel_order ' + order_id.encode() + b'\n')
            break
    sock.close()
