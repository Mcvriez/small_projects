from datetime import datetime
from fxcmpy import ServerError
import peewee
import pymysql
import os
import sys
import xlwt

from mt4ExposureChecker.src.lp_positions import lp_positions
from mt4ExposureChecker.src.mt_positions import mt4_positions
from mt4ExposureChecker.src.config import access_config


def compare():
    db_params = access_config.db_params
    connections = access_config.connections
    print('Configuration files located, connecting..')
    for connection in connections:
        dbname = connection['db']
        groups = connection['groups']
        token = connection['token']
        name = connection['name']
        print(f"\nRetrieving data for {name}:")
        try:
            mt_pos = mt4_positions(groups, dbname, db_params)
            lp_pos = lp_positions(token)
            pos = compile_positions(mt_pos, lp_pos)
            dump_to_excel(pos, name)
        except (pymysql.err.InternalError, peewee.InternalError):
            e = sys.exc_info()[1]
            print(f'Error ({e}) occurred while connecting to {name}')
        except ValueError:
            e = sys.exc_info()
            print(f'ValueError ({e}) occurred while connecting to {name}')
        except OSError:
            e = sys.exc_info()
            print(f"OS error: {e}")
        except ServerError:
            print(f'FXCM refused connection with error for the token {token}')
    os._exit(0)


def compile_positions(mt_pos, lp_pos):
    for item in lp_pos.keys():
        if item in mt_pos:
            mt_pos[item]['lp_vol'] = lp_pos[item]
        else:
            mt_pos[item] = {'mt_lots': 0, 'mt_vol': 0, 'lp_vol': lp_pos[item]}
    return mt_pos


def dump_to_excel(pos, sheetname):
    folder_name = r'reports\\' + datetime.now().strftime('_%m-%d')
    time = datetime.now().strftime(' %H_%M')
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    path = folder_name + r'\\' + sheetname + time + '.xls'
    print(f'Creating file {path}')
    xls_header = ['Symbol', 'Mt4 volume (lots)', 'Mt4 to FXCM vol', 'Real FXCM volume', 'Diff (FXCM contracts)']
    book = xlwt.Workbook()
    # Styling:
    style_header = xlwt.easyxf('font: name Leelawadee, color-index black, bold on, height 250; align: vertical center, horizontal center, wrap on;')
    style_table = xlwt.easyxf('align: vertical center, horizontal center,wrap on;')
    style_diff = xlwt.easyxf('pattern: pattern solid, fore_color gray25; font: color black, bold on; align: vertical center, horizontal center,wrap on;')
    sh = book.add_sheet(sheetname)
    sh.row(0).height_mismatch = True
    sh.row(0).height = 256*3
    sh.col(0).width = 256*25
    sh.col(1).width = 256*25
    sh.col(2).width = 256*25
    sh.col(3).width = 256*25
    sh.col(4).width = 256*28

    if pos:
        for n, symbol in enumerate(pos):
            diff = pos[symbol]['mt_vol'] - pos[symbol]['lp_vol']
            if n == 0:
                for i, item in enumerate(xls_header):
                    sh.write(0, i, item, style_header)
            sh.write(n + 1, 0, symbol, style_table)
            sh.write(n + 1, 1, pos[symbol]['mt_lots'], style_table)
            sh.write(n + 1, 2, pos[symbol]['mt_vol'], style_table)
            sh.write(n + 1, 3, pos[symbol]['lp_vol'], style_table)
            if diff:
                sh.write(n + 1, 4, diff , style_diff)
            else:
                sh.write(n + 1, 4, diff, style_table)
        book.save(path)
    else:
        print('There are no positions on Mt4 and liquidity, creating empty report..')
        for i, item in enumerate(xls_header):
            sh.write(0, i, item, style_header)
        book.save(path)





