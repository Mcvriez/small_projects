import yaml
import pandas
import time
from datetime import timedelta, datetime
from pytz import timezone
from sqlalchemy import create_engine, exc
import slackmsg as slack
from types import SimpleNamespace
import os
import sys
import urllib.error
import logging
from threading import Thread
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import api
import re

location = os.path.dirname(sys.argv[0])
cfg = SimpleNamespace(**yaml.load(open(f"{location}/monitor/config.yaml"), Loader=yaml.FullLoader))
logging.basicConfig(level=cfg.logging_level, format='%(levelname)s:%(asctime)s %(message)s',
                    datefmt='%Y/%m/%d %H:%M:%S')


SYMBOL_DELAY_CACHE = {}  # symbol -> timestamp


def is_market(time_now):
    if time_now.weekday() in (5, 6):
        return False
    elif time_now.date in cfg.holidays:
        return False
    elif time_now.hour == 0:
        if time_now.minute < 6:
            return False
    return True


def low_volatility_multiplier(time_now):
    if time_now.hour == 0:
        if time_now.minute < 30:
            return 5
        return 3
    if time_now.hour < 3:
        return 2
    if time_now.hour == 23 and time_now.minute > 15:
        return 2
    return 1


def send_alert(data):
    logging.warning(f'slack msg - {data}')
    try:
        slack.send(cfg, data)
    except urllib.error.URLError as e:
        logging.error(f'Slack message sending fail: {e}')


def send_delayed_symbols(df, time_now):
        for index, row in df.iterrows():
            template = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{row.symbol}* doesn't work since {time_now.strftime('%H:%M')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "chart"
                        },
                        "value": f"{row.symbol}",
                        "action_id": "chart"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "silence for a day"
                        },
                        "value": f"{row.symbol}",
                        "action_id": "silence_symbol",
                        "style": "danger"
                    },
                ]
            }
            ]
            try:
                slack.send(cfg, blocks=template, text=f"*{row.symbol}* since {time_now.strftime('%H:%M')}")
            except urllib.error.URLError as e:
                logging.error(f'Slack message sending fail: {e}')


def delay_lambda(row, time_now, delay_multiplier=1):
    symbol = row.symbol.replace('.ecn', '')
    allowed_delay = cfg.extra_delays.get(symbol, cfg.max_delay_single_symbol) * delay_multiplier

    if symbol in cfg.first_hour_skip:
        if time_now.hour == 0 or (time_now.hour == 1 and time_now.minute < 15):
            return False
    if symbol == 'ES35':
        if time_now.hour <= 9 or time_now.hour >= 21:
            return False
    if symbol == 'UKOil':
        if time_now.hour <= 3:
            return False
    if symbol in SYMBOL_DELAY_CACHE:
        logging.debug(f'{row.symbol} was reported recently, skipping.')
        return False
    if row.delay > allowed_delay:
        logging.debug(f'adding {row} to cache')
        SYMBOL_DELAY_CACHE[symbol] = int(time.time()) + 10800  # 3 hours silence
        return True
    return False


def quote_delay(quotes, time_now):
    delay_multiplier = low_volatility_multiplier(time_now)
    quotes['delay'] = quotes.apply(lambda x: (time_now - x.time).seconds, axis=1)
    quotes['alert_flag'] = quotes.apply(lambda x: delay_lambda(x, time_now, delay_multiplier), axis=1)
    quotes.drop(columns=['time'], inplace=True)
    logging.debug(quotes.to_string(index=False, header=False))
    quotes = quotes[quotes.alert_flag].copy()
    quotes.drop(columns=['alert_flag'], inplace=True)
    if not quotes.empty:
        send_delayed_symbols(quotes, time_now)


def clear_delay_cache():
    ctime = int(time.time())
    for symbol, delay in SYMBOL_DELAY_CACHE.copy().items():
        if ctime > delay:
            logging.debug(f'removing symbol {symbol} from cache due to expiration')
            SYMBOL_DELAY_CACHE.pop(symbol, 0)

    if SYMBOL_DELAY_CACHE: logging.debug(SYMBOL_DELAY_CACHE)


def slack_listener():
    app = App(token=cfg.slack_token)

    @app.action("silence_symbol")
    def handle_action(ack, action, respond, body):
        symbol = action['value']
        new_timestamp = int(time.time()) + 86400
        s_timestamp = (datetime.fromtimestamp(new_timestamp)).strftime('%B %d %H:%M')
        ack()
        template = [{
            "type": "section",
            "text": {
                        "type": "mrkdwn",
                        "text": f"*{symbol}* notifications were silenced until {s_timestamp} by @{body['user']['name']}"
                    }
        }]
        respond(blocks=template)  # replace_original=True
        SYMBOL_DELAY_CACHE[symbol] = new_timestamp

    @app.action("chart")
    def handle_action(ack, action,  body):
        symbol = action['value']
        eastern = timezone('US/Eastern')
        utc = timezone('utc')
        now = datetime.now()
        delta = (eastern.localize(now) - utc.localize(now)).seconds - 3600  # 3 or 4 hours
        ts = int(body.get('container').get('message_ts').split('.')[0])
        ts_mt = ts + delta

        ack()
        image = api.get_charts(cfg, symbol=symbol, ts=ts_mt, chart_period=7200, size=5)
        if image:
            logging.info(slack.send_file(symbol, cfg, rf"{location}/monitor/images/{image}.png"))
        else:
            logging.error('unable to get charts from mt4')

    @app.message("clear")
    def handle_clear(message, say):
        global SYMBOL_DELAY_CACHE
        say(f'clearing cache: {SYMBOL_DELAY_CACHE}')
        SYMBOL_DELAY_CACHE = {}

    @app.message("cache")
    def handle_show(message, say):
        msg = ([f"{symbol} {(datetime.fromtimestamp(ts)).strftime('%B %d %H:%M')}" for symbol, ts in SYMBOL_DELAY_CACHE.items()])
        msg = '\n'.join(msg) or 'symbol cache is empty'
        say(msg)

    @app.message("reload")
    def handle_show(message, say):
        global cfg
        cfg = SimpleNamespace(**yaml.load(open(f"{location}/monitor/config.yaml"), Loader=yaml.FullLoader))
        say('config was reloaded')

    @app.message(re.compile(r"(chart.*)"))
    def say_hello_regex(say, context):
        # regular expression matches are inside of context.matches
        greeting = context['matches'][0].split(' ')
        for symbol in greeting:
            if symbol in cfg.symlist:
                image = api.get_charts(cfg, symbol=symbol, chart_period=3600*24, size=60)
                slack.send_file(symbol, cfg, rf"{location}/monitor/images/{image}.png")
                # break

    @app.message("delays")
    def handle_show(message, say):
        say(f'default delay: {cfg.max_delay_all_quotes}, '
            f'single symbol: {cfg.max_delay_single_symbol}, '
            f'trades: {cfg.max_delay_trades}\nextra delays:\n')
        say(str(cfg.extra_delays))

    @app.event("message")
    def handle_message_events(message, logger):
        logger.info(message)

    SocketModeHandler(app, cfg.apptoken).start()


def routine():
    engine = create_engine(cfg.rs)
    issue_flag = False
    max_delay_quotes = timedelta(seconds=cfg.max_delay_all_quotes)
    max_delay_trades = timedelta(seconds=cfg.max_delay_trades)

    while True:
        if issue_flag:
            logging.warning('major incident - going to sleep for one hour')
            time.sleep(3600)
            logging.info('recovering from sleep')
            issue_flag = False

        time_now = datetime.now()
        clear_delay_cache()

        try:
            quotes = pandas.read_sql_query(f'select symbol, time from {cfg.quotes_table}', engine)
            quotes = quotes[quotes.symbol != 'BTCUSD']
            last_quote = quotes.time.max()
            last_operation = pandas.pandas.read_sql_query(
                f'select max(OPEN_TIME) mtime from {cfg.trades_table}', engine).iloc[0]['mtime']

            quotes_filter = time_now - max_delay_quotes
            delay = quotes.loc[(quotes.time < quotes_filter)]
            delay_no_ecn = delay.loc[~(delay.symbol.str.contains('ecn'))]
            delay_ecn = delay.loc[(delay.symbol.str.contains('ecn'))]

            ecn_equality_flag = delay_no_ecn.reset_index(drop=True) \
                .time.equals(delay_ecn.reset_index(drop=True).time)
            if ecn_equality_flag:
                delay = delay_no_ecn

            if is_market(time_now):
                if time_now - last_operation > max_delay_trades:
                    logging.info(f'last operation: {last_operation}')
                    depo_fail = api.operation_fails(cfg)
                    if depo_fail:
                        send_alert(f'{depo_fail} {cfg.mt_admin} {cfg.mt_dealing}')
                        issue_flag = True
                elif time_now - last_quote > max_delay_quotes:
                    send_alert(f'all quotes on mt4 are not working. server is operational. {cfg.mt_admin} {cfg.mt_dealing}')
                    issue_flag = True
                elif not delay.empty and not issue_flag:
                    quote_delay(delay, time_now)

        except exc.OperationalError as e:
            engine = create_engine(cfg.rs)
            send_alert(f'report server connection error:\n{exc} {cfg.mt_admin}')
            issue_flag = True
            continue
        time.sleep(cfg.repeat_time)


if __name__ == '__main__':
    t1 = Thread(target=slack_listener, name='slack_thread')
    t2 = Thread(target=routine, name='monitor_thread')
    t1.start()
    t2.start()

