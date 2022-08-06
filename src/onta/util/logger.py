import datetime 

class Logger():

    levels = [
        'MAXIMUM_OVERDRIVE',
        'INFINITE',
        'VERBOSE',
        'DEBUG',
        'INFO',
    ]

    def __init__(self, location, log_level="INFO"):
        self.location = location
        self.log_level = log_level

    # LOGGING FUNCTIONS
    def comment(self, msg, method, level="INFO"):
        now = datetime.datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        print(dt_string, ' : ', level, ':',
              f'{self.location}.{method}', ' : ', msg)

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

