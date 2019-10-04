import os
from fxcmSwaps.src.fxcmconnector import FXCMConnector


def dump_result(output, swap_dict):
    header = 'symbol:rollB:rollS\n'
    if os.path.exists(output):
        os.remove(output)
    with open(output, 'w') as file:
        file.write(header)
        for key, value in swap_dict.items():
            file.write(f'{key}:{value[0]}:{value[1]}\n')


def routine(token, output, log='', log_level='', verbose=False):
    print('connecting to fxcm..')
    sc = FXCMConnector(token, log_file=log, log_level=log_level, verbose=verbose)
    print('requesting swaps..')
    sc.get_all_swaps()
    print(f'writing result to: {output}')
    dump_result(output, sc.swaps)
    print(f'operation is completed, closing..')
    os._exit(0)
