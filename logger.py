import logging
import sys


class LogFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level


def init_logger(logger_name):
    log = logging.getLogger(logger_name)
    log.setLevel(logging.DEBUG)
    
    fh = logging.FileHandler('C:/Users/mus-k/Desktop/Üniversite/Tez/Node Red/nodes2/pythonlog.log')
    fh.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d - %H:%M:%S")
    fh.setFormatter(file_formatter)
    log.addHandler(fh)
    
    oh = logging.StreamHandler(sys.stdout)
    oh.setLevel(logging.INFO)
    oh.addFilter(LogFilter(logging.INFO))
    oh_formatter = logging.Formatter(fmt="%(message)s")
    oh.setFormatter(oh_formatter)
    log.addHandler(oh)

    eh = logging.StreamHandler(sys.stderr)
    eh.setLevel(logging.ERROR)
    eh.addFilter(LogFilter(logging.ERROR))
    eh_formatter = logging.Formatter(fmt="%(message)s")
    eh.setFormatter(eh_formatter)
    log.addHandler(eh)
    
    return log
