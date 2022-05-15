import time
import socket
import logging
import pandas as pd
from io import StringIO
from datetime import datetime
import plotly.graph_objects as go
import os
import sys

location = os.path.dirname(sys.argv[0])


def _wikmsg(host, port, req='action=servertime'):
    try:
        with socket.socket() as s:
            s.settimeout(15)
            s.connect((host, port))
            sock_file = s.makefile('rwb')
            sock_file.write(req.encode('utf-8'))
            sock_file.flush()
            count = sock_file.readline()
            datamsg = sock_file.read(int(count)).decode()
        if 'result=1' in datamsg:
            logging.info(f'successful wik request: {req}')
        else:
            logging.warning(req)
            logging.warning(datamsg)
    except (ConnectionRefusedError, socket.timeout, ValueError) as e:
        return {'result': -1, 'error': e}
    return dict((key, value) for key, value in (pair.split('=') for pair in datamsg.split('&')))


def operation_fails(cfg, tries=3):
    host = cfg.wik['host']
    port = cfg.wik['port']
    account = cfg.wik["test_account"]
    max_tries = tries
    req = f'action=changebalance&login={account}&comment=monitoring operation&value=0.01'
    while tries:
        tries -= 1
        result = _wikmsg(host, port, req)
        if result.get('result', 0) == '1':
            return False
        if result.get('result', 0) != '1':
            logging.warning(f'api error on response attempt {max_tries - tries}')
        if not tries:
            logging.warning(result)
            if 'error' in result:
                return 'api can\'t connect to mt4. server is unreachable'
            else:
                return 'api interaction error. server could be frozen'
        time.sleep(cfg.sleep_on_trade_fail)


def get_charts(cfg, ts=0, symbol='EURDKK', chart_period=3600, size=1):
    host = cfg.wik['host']
    port = cfg.wik['port']
    try:
        stime = int(_wikmsg(host, port).get('time', 0))
    except (ValueError, AttributeError):
        logging.warning('time request fails')
        return 0
    if stime - ts < chart_period or ts == 0:
        tfrom = stime - chart_period
    else:
        tfrom = ts
        stime = ts + chart_period
    charts_req = f"action=getcharthistory&symbol={symbol}&from={tfrom}&to={stime}&size={size}"
    charts = _wikmsg(host, port, charts_req)
    data = charts.get('count', '')
    if data:
        data = (pd.read_csv(StringIO(data), delimiter=';', header=0,
                            names=['open', 'close', 'low', 'high', 'timestamp', 'volume']))
        data.timestamp = data.apply(lambda x: datetime.utcfromtimestamp(x.timestamp), axis=1)
        fig = go.Figure(data=[go.Candlestick(x=data.timestamp,
                                             open=data.open,
                                             high=data.high,
                                             low=data.low,
                                             close=data.close,
                                             increasing_line_color='white',
                                             decreasing_line_color='black')])
        fig.update_layout(xaxis_rangeslider_visible=False, legend_font=dict(family="Courier New", size=400))
        cs = fig.data[0]
        cs.increasing.line.color = 'black'
        cs.increasing.fillcolor = 'white'

        fig.write_image(rf"{location}/monitor/images/{stime}.png", width=1920, height=1080)
        return stime
    return 0







































