# -*- coding: utf-8 -*-
import os
import logging
import logzero
from logzero import logger, LogFormatter


DEBUG = True

TEMP_DIR = os.path.join(os.getcwd(), 'temp')
TEST_DATA_DIR = os.path.join(os.getcwd(), 'test_data')

WORKING_DIR = '/crazybox/'

if not os.path.isdir(TEMP_DIR):
    os.mkdir(TEMP_DIR)

if not os.path.isdir(TEST_DATA_DIR):
    os.mkdir(TEST_DATA_DIR)

CPU_TO_REAL_TIME_FACTOR = 3

DEFAULT_GENERATE_FILE_SIZE = 256 * 1024 * 1024  # 256M

DEFAULT_LIMITS = {
    # CPU time in seconds, None for unlimited
    'cpu_time': 1,
    # Real time in seconds, None for unlimited
    'real_time': 5,
    # Memory in megabytes, None for unlimited
    'memory': 64,

    # Allow user process to fork
    # 'can_fork': False,
    # Limiting the maximum number of user processes in Linux is tricky.
    # http://unix.stackexchange.com/questions/55319/are-limits-conf-values-applied-on-a-per-process-basis
}

if DEBUG:
    logzero.loglevel(logging.DEBUG)
else:
    logzero.loglevel(logging.WARNING)


fmt = '%(color)s[%(asctime)s <%(module)s:%(funcName)s>:%(lineno)d] [%(levelname)s]%(end_color)s - %(message)s'
formatter = LogFormatter(color=True, datefmt='%Y%m%d %H:%M:%S', fmt=fmt)

logzero.formatter(formatter)

logzero.logfile(filename='crazybox.log', maxBytes=1000000, backupCount=3, loglevel=logging.WARNING)

logger.debug("start crazybox")


def fuc():
    logger.debug("start fuc")


if __name__ == '__main__':
    print("中文测试 " + os.path.join(os.getcwd(), 'tmp'))
    fuc()
