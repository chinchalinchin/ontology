import numba
from numba.experimental import jitclass


spec = [
    ('levels', numba.types.List(numba.types.string)), 
    ('location', numba.types.string),
    ('log_level', numba.types.string), 
]

@jitclass(spec)
class Logger():

    def __init__(self, location, log_level="INFO"):
        self.location = location
        self.log_level = log_level
        self.levels = [
            'MAXIMUM_OVERDRIVE',
            'INFINITE',
            'VERBOSE',
            'DEBUG',
            'INFO',
        ]


    def comment(self, msg, method, level="INFO"):
        # now = datetime.datetime.now()
        # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        print(">> ", level, ':', f'{self.location}.{method}')
        print('\t\t\t\t\t', msg)


    def error(self, msg, method):
        self.comment(msg, method, 'ERROR',)


    def info(self, msg, method):
        if self.log_level in self.levels:
            self.comment(msg, method, self.levels[4])


    def debug(self, msg, method):
        if self.log_level in self.levels[:4]:
            self.comment(msg, method, self.levels[3])


    def verbose(self, msg, method):
        if self.log_level in self.levels[:3]:
            self.comment(msg, method, self.levels[2])


    def infinite(self, msg, method):
        if self.log_level in self.levels[:2]:
            self.comment(msg, method, self.levels[1])


    def maximum_overdrive(self, msg, method):
        if self.log_level in self.levels[:1]:
            self.comment(msg, method, self.levels[0])

