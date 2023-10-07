from datetime import datetime

class LogHelper:
    def __init__(self):
        pass

    def debug(self, message):
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} DEBUG: {message}')

    def info(self, message):
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} INFO: {message}')

    def warning(self, message):
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} WARNING: {message}')

    def error(self, message):
        print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ERROR: {message}')