from typing import Union
import decimal
from decimal import (
    localcontext,
)


MIN_WEI = 0
MAX_WEI = 2**256 - 1


def format_uints(number: int, decimals: int) -> Union[int, decimal.Decimal]:
    """
    Takes a number of wei and converts it to any other unit.
    """
    if number == 0:
        return 0

    if number < MIN_WEI or number > MAX_WEI:
        raise ValueError('value must be between 0 and 2**256 - 1')

    unit_value = decimal.Decimal(10) ** decimals

    with localcontext() as ctx:
        ctx.prec = 999
        d_number = decimal.Decimal(value=number, context=ctx)
        result_value = d_number / unit_value

    return result_value


def parse_uints(number: Union[int, float, str, decimal.Decimal], decimals: int) -> int:
    """
    Takes a number of a unit and converts it to wei.
    """
    if decimals < 1:
        raise ValueError('Decimals must be greater than 0')

    if isinstance(number, int) or isinstance(number, str):
        d_number = decimal.Decimal(value=number)
    elif isinstance(number, float):
        d_number = decimal.Decimal(value=str(number))
    elif isinstance(number, decimal.Decimal):
        d_number = number
    else:
        raise TypeError('Unsupported type. Must be one of integer, float, or string')

    s_number = str(number)
    unit_value = decimal.Decimal(10) ** decimals

    if d_number == decimal.Decimal(0):
        return 0

    if d_number < 1 and '.' in s_number:
        with decimal.localcontext() as ctx:
            multiplier = len(s_number) - s_number.index('.') - 1
            ctx.prec = multiplier
            d_number = decimal.Decimal(value=number, context=ctx) * 10**multiplier
        unit_value /= 10**multiplier

    with decimal.localcontext() as ctx:
        ctx.prec = 999
        result_value = decimal.Decimal(value=d_number, context=ctx) * unit_value

    if result_value < MIN_WEI or result_value > MAX_WEI:
        raise ValueError('Resulting wei value must be between 0 and 2**256 - 1')

    return int(result_value)
