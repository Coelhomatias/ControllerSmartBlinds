import platform
import datetime as dt


class _AnsiColorStreamHandler():
    DEFAULT = '\x1b[0m'
    RED = '\x1b[31m'
    GREEN = '\x1b[32m'
    YELLOW = '\x1b[33m'
    CYAN = '\x1b[36m'

    CRITICAL = RED
    ERROR = RED
    WARNING = YELLOW
    INFO = GREEN
    DEBUG = CYAN

    def __init__(self, name):
        self._name = name

    def log(self, level, message):
        if level == 'debug':
            levelname = 'D'
            color = self.DEBUG
        elif level == 'info':
            levelname = 'I'
            color = self.INFO
        elif level == 'warning':
            levelname = 'W'
            color = self.WARNING
        elif level == 'error':
            levelname = 'E'
            color = self.ERROR
        elif level == 'critical':
            levelname = 'C'
            color = self.CRITICAL

        time = str(dt.datetime.now().hour) + ':' + str(dt.datetime.now().minute) + ':' + \
            ('00' if dt.datetime.now().second ==
             0 else str(dt.datetime.now().second))
        text = '[' + time + '][' + levelname + \
            '][' + self._name + ']: ' + message
        print(color + text + self.DEFAULT)


class _WinColorStreamHandler():
    # wincon.h
    FOREGROUND_BLACK = 0x0000
    FOREGROUND_BLUE = 0x0001
    FOREGROUND_GREEN = 0x0002
    FOREGROUND_CYAN = 0x0003
    FOREGROUND_RED = 0x0004
    FOREGROUND_MAGENTA = 0x0005
    FOREGROUND_YELLOW = 0x0006
    FOREGROUND_GREY = 0x0007
    FOREGROUND_INTENSITY = 0x0008  # foreground color is intensified.
    FOREGROUND_WHITE = FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED

    BACKGROUND_BLACK = 0x0000
    BACKGROUND_BLUE = 0x0010
    BACKGROUND_GREEN = 0x0020
    BACKGROUND_CYAN = 0x0030
    BACKGROUND_RED = 0x0040
    BACKGROUND_MAGENTA = 0x0050
    BACKGROUND_YELLOW = 0x0060
    BACKGROUND_GREY = 0x0070
    BACKGROUND_INTENSITY = 0x0080  # background color is intensified.

    DEFAULT = FOREGROUND_WHITE
    CRITICAL = BACKGROUND_YELLOW | FOREGROUND_RED | FOREGROUND_INTENSITY | BACKGROUND_INTENSITY
    ERROR = FOREGROUND_RED | FOREGROUND_INTENSITY
    WARNING = FOREGROUND_YELLOW | FOREGROUND_INTENSITY
    INFO = FOREGROUND_GREEN
    DEBUG = FOREGROUND_CYAN

    def __init__(self, name):
        self._name = name

    def log(self, level, message):
        if level == 'debug':
            levelname = 'D'
        elif level == 'info':
            levelname = 'I'
        elif level == 'warning':
            levelname = 'W'
        elif level == 'error':
            levelname = 'E'
        elif level == 'critical':
            levelname = 'C'

        time = str(dt.datetime.now().hour) + ':' + str(dt.datetime.now().minute) + ':' + \
            ('00' if dt.datetime.now().second ==
             0 else str(dt.datetime.now().second))
        text = '[' + time + '][' + levelname + \
            '][' + self._name + ']: ' + message
        print(text)


# select ColorStreamHandler based on platform
if platform.system() == 'Windows':
    ColorLogger = _WinColorStreamHandler
else:
    ColorLogger = _AnsiColorStreamHandler
