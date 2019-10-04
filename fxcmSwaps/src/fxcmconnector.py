import fxcmpy


class FXCMConnector:
    def __init__(self, token, log_level='', log_file='', verbose=False):
        self.token = token
        self.log_level = log_level
        self.log_file = log_file
        self.connect = fxcmpy.fxcmpy(token, log_level=log_level, log_file=log_file)
        self.instruments = self.connect.get_instruments()
        self.subscription_step = 10
        self.verbose = verbose
        self.swaps = {}

    def _reconnect(self):
        self.connect.close()
        if self.verbose: print('reconnecting..')
        self.connect = fxcmpy.fxcmpy(self.token, log_level=self.log_level, log_file=self.log_file)

    def _subscribe(self, inst_list):
        for i in inst_list:
            ret = self.connect.subscribe_instrument(i)
            if self.verbose: print(f'subscribing {i}: {ret}')

    def _unsubscribe(self, inst_list):
        for i in inst_list:
            ret = self.connect.unsubscribe_instrument(i)
            if self.verbose: print(f'unsubscribing {i}: {ret}')

    def _get_swap_update(self):
        if self.verbose: print('getting offers')
        offer = self.connect.get_offers(kind='list')
        if self.verbose: print(offer)
        for item in offer:
            if item['currency'] not in self.swaps:
                self.swaps[item['currency']] = [item['rollB'], item['rollS']]

    def get_all_swaps(self):
        while len(self.swaps) < len(self.instruments):
            self._get_swap_update()
            done = list(self.swaps.keys())
            self._unsubscribe(done[-self.subscription_step:])
            remains = list(set(self.instruments) - set(done))
            self._subscribe(remains[:self.subscription_step])
            self._reconnect()
        self.connect.close()
