import configparser
from dataclasses import dataclass
import sys
import time


gconfig = configparser.ConfigParser()
gconfig.read(r'configuration\config.ini')


@dataclass
class Symbol_map:
    try:
        _s_map = gconfig['Maps']['map']
        _mconfig = configparser.ConfigParser()
        _mconfig.read(_s_map)
        contract_sizes = _mconfig['ContractSizes']
        contract_mult = _mconfig['ContractMultipliers']
        instruments = _mconfig['Instruments']
    except KeyError:
        print('Configuration files are missing / corrupted.\nPlease check files <config.ini> and <symbol_map.ini> can be '
              'found in the <configuration> folder and contain all necessary data.\nApplication will be closed.')
        time.sleep(10)
        sys.exit(1)


@dataclass
class Connections:
    db_params = dict(gconfig._sections['ReportServer'])
    db_params['port'] = int(db_params['port'])
    db_params['use_unicode'] = bool(db_params['use_unicode'])
    connections = []
    for connect in gconfig.sections():
        if connect != 'ReportServer' and connect != 'Maps':
            params = dict(gconfig._sections[connect])
            params['groups'] = params['groups'].split(';')
            params['name'] = connect
            connections.append(params)


map_config = Symbol_map()
access_config = Connections()
