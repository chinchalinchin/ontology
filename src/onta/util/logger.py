import datetime 

class Logger():

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
        if self.log_level in ['INFO', 'DEBUG', 'VERBOSE', 'INFINITE']:
            self.comment(msg, method, 'INFO')

    def debug(self, msg, method):
        if self.log_level in ['DEBUG', 'VERBOSE', 'INFINITE']:
            self.comment(msg, method, 'DEBUG')

    def verbose(self, msg, method):
        if self.log_level in ['VERBOSE', 'INFINITE']:
            self.comment(msg, method, 'VERBOSE')

    def infinite(self, msg, method):
        if self.log_level == 'INFINITE':
            self.comment(msg, method, 'INFINITE')
