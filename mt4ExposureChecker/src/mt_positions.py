from datetime import datetime
from src.reportserver import get_trades, get_users
from src.config import map_config


def mt4_positions(groups, dbname, dbparams):
    users_table, trades_table = db_init(dbname, dbparams)
    user_list = get_user_list(users_table, groups)
    orders = get_open_orders(user_list, trades_table)
    positions = zip_orders(orders)
    return positions


def db_init(dbname, dbparams):
    trades = get_trades(dbname, dbparams)
    users = get_users(dbname, dbparams)
    return users, trades


def get_user_list(users_table, groups):
    user_list = []
    for group in groups:
        users = users_table.select().where(users_table.group == group)
        user_list += [user.login for user in users]
    return user_list


def get_open_orders(user_list, trades_table):
    open_orders = []
    null_time = datetime(1970, 1, 1, 0, 0, 0)    # open orders have this date as a close time
    for user in user_list:
        user_trades = trades_table.select().where(
            trades_table.login == user,
            trades_table.close_time == null_time,
            trades_table.cmd < 2)               # only buy and sell
        if user_trades:
            open_orders += [trade for trade in user_trades]
    return open_orders


def zip_orders(order_list):
    positions = {}
    cs = map_config.contract_sizes
    cm = map_config.contract_mult
    lp_instruments = map_config.instruments
    for order in order_list:
        symbol = lp_instruments[order.symbol]
        volume = order.volume
        mult = 1 if order.cmd == 0 else -1
        lp_mult = mult
        if symbol in cs:
            lp_mult = mult * int(cs[symbol]) / 100 / float(cm[symbol])   # harmonize to lp positions
        if symbol not in positions:
            positions[symbol] = {'mt_lots': volume * mult / 100, 'mt_vol': volume * lp_mult}
        else:
            positions[symbol]['mt_lots'] += volume * mult / 100
            positions[symbol]['mt_vol'] += volume * lp_mult
        positions[symbol]['lp_vol'] = 0
    return positions
