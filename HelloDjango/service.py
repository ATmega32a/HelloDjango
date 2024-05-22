def parse_car_number(string: str):
    result = ''
    words_dict = {
        'А': 'A',
        'В': 'B',
        'Е': 'E',
        'І': 'I',
        'К': 'K',
        'М': 'M',
        'Н': 'H',
        'О': 'O',
        'Р': 'P',
        'С': 'C',
        'Т': 'T',
        'У': 'Y',
        'Х': 'X'
    }

    for word in string.upper():
        try:
            result += words_dict[word]
        except KeyError:
            result += word
    return result
