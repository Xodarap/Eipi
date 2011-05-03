import math

class utils:
    @staticmethod
    def int_to_base64(x):
        if x == 0:
            return ''
        this_digit = x % 64
        remaining = math.floor(x / 64)
        this_char = utils.encode_digit(this_digit)
        return utils.int_to_base64(remaining) + this_char

    @staticmethod
    def encode_digit(x):
        if x == 63:
            return '-'
        elif x == 62:
            return '_'
        elif x >= 52:   # 52-61 -> 0-9
            return str(x-52)
        elif x >= 25:   # 25-50 -> A-Z
            return chr(x + 40)
        else:           # 0-24  -> a-z
            return chr(x + 97)
        

