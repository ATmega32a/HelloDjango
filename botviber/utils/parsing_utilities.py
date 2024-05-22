def parse_car_number(string: str):
    words_dict_ru = dict(А='A', В='B', Е='E', І='I', К='K', М='M', Н='H', О='O', Р='P', С='C', Т='T', У='Y', Х='X')
    words_dict_en = {v: k for k, v in words_dict_ru.items()}

    def reverse_lang_word(words_dict: {}):
        result = ''
        for word in string.upper():
            try:
                result += words_dict[word]
            except KeyError:
                result += word
        return result
    return reverse_lang_word(words_dict_ru), reverse_lang_word(words_dict_en)


def normalize_snils(snils):
    snils = str(snils)
    while len(snils) < 11:
        snils = '0' + snils
    snils = f'{snils[0:3]}-{snils[3:6]}-{snils[6:9]} {snils[9:11]}'
    return snils


def check_snils(snils):
    if len(snils) != 14:
        return False

    def snils_csum(snils):
        k = range(9, 0, -1)
        pairs = zip(k, [int(x) for x in snils.replace('-', '').replace(' ', '')[:-2]])
        return sum([k * v for k, v in pairs])

    csum = snils_csum(snils)

    while csum > 101:
        csum %= 101
    if csum in (100, 101):
        csum = 0

    return csum == int(snils[-2:])
