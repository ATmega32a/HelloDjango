from viberbot import Api, BotConfiguration

from properties import auth_token

viber = Api(BotConfiguration(
    name='Оператор Елена',
    avatar='https://viberbot.ru/scr/oper.jpg',
    auth_token=auth_token
))
