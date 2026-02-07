from time import time_ns, sleep
import math


class Throttle:
    '''A class for throttling requests'''

    _sec = 10**9
    _min = _sec * 60
    _penaltyCount = 0

    def __init__(self, config: dict, maxPenaltyCount: int):
        '''Initialise Throttle

        Params:
        config - A dictionary containing endpoint as keys and dictionary values
                defining rps (requests per second) and rpm (requests per minute)
                {
                    'some_endpoint': {
                        'rps': 15,
                    },
                    'default': {
                        'rps': 3,
                        'rpm': 200
                    }
                }

        max_penalty_count - Max number of acceptable 429 http codes.
                            Throttle.penalise method must be called everytime
                            a 429 http code is returned from a request to
                            keep track.

        '''
        ts = time_ns()

        for d in config.values():
            d['start'] = ts
            d['count'] = 0

        self.maxPenaltyCount = maxPenaltyCount
        self.config = config

    @staticmethod
    def _round(x, base) -> float:
        '''Utility method to round to nearest base'''

        return math.ceil(x / base) * base

    def penalize(self) -> bool:
        '''Sleep 1 second on too many requests.
        Returns True if penalty_count exceeds limit'''

        self._penaltyCount += 1
        print('Too many requests to the API')
        sleep(1)
        return self._penaltyCount > self.maxPenaltyCount

    def check(self, key='default'):
        '''Check if api limit exeeded

        Params:
        key - The endpoint to be throttled. Key is 'default' if not specified'''

        k = self.config[key]
        k['count'] += 1

        if 'rpm' in k and k['count'] % k['rpm'] == 0:
            elapsed_time = time_ns() - k['start']
            tt_nxt_min = self._round(elapsed_time, self._min) - elapsed_time
            return sleep(tt_nxt_min / self._sec)

        if k['count'] % k['rps'] == 0:
            elapsed_time = time_ns() - k['start']
            tt_nxt_sec = self._round(elapsed_time, self._sec) - elapsed_time
            return sleep(tt_nxt_sec / self._sec)
