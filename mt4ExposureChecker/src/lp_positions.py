from fxcmpy import fxcmpy
from src.config import map_config


def get_orders(token):
    con = fxcmpy(access_token=token, log_level='error', server='real')
    return con.get_open_positions(kind='list')


def zip_orders(order_list):
    result = {}
    cs = map_config.contract_sizes
    if order_list:
        for order in order_list:
            mult = 1 if order['isBuy'] else -1
            curr = order['currency']
            amount = order['amountK']
            if curr in cs:
               mult *= 1000  # FXCM provides amounts in thouthands, but shows in direct quantity
            if curr not in result:
                result[curr] = round(mult * float(amount), 2)
            else:
                result[curr] += round(mult * float(amount), 2)
    return result


def lp_positions(token):
    orders = get_orders(token)
    return zip_orders(orders)



