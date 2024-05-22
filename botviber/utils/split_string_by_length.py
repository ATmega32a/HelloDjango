import re


def split_string_by_length(string: str, length: int) -> list:
    array_of_pieces_string = []
    short_text = ''
    for word in re.sub('[\\s]+', ' ', string.lstrip()).split(' '):
        if len(short_text + word) >= length:
            array_of_pieces_string.append(short_text)
            short_text = word + ' '
        else:
            short_text += word + ' '
    array_of_pieces_string.append(short_text.rstrip())

    return array_of_pieces_string