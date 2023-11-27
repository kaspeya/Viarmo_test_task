import datetime
import logging
import os
import traceback
from logging.handlers import RotatingFileHandler

TRACE_LEVEL = 5


def add_log_level_trace(logger):
    if not hasattr(logger, 'trace'):
        logging.addLevelName(TRACE_LEVEL, 'TRACE')


def init_file_log(activity, path, level, rotate=True, rotate_size=100 * 1024 * 1024, rotate_backup=1):
    """
    log initializer. Inits  log to to file
    :param activity: prefix for log
    :param path: path to save log
    :param level: log level (string)
    :return:logger
    """
    current_process_id = os.environ.get('PROCESS_LABEL', '')
    if current_process_id != '':
        current_process_id = '[' + current_process_id + ']'

    logger = logging.getLogger()
    add_log_level_trace(logger)
    logger.setLevel(0)  # take all in root
    dt = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M')
    if not os.path.exists(path):
        os.mkdir(path)
    name = os.path.join(path, '{}_{}_{}.log'.format(activity, current_process_id, dt))
    if rotate:
        fh = RotatingFileHandler(
            name,
            maxBytes=rotate_size,
            backupCount=rotate_backup,
            encoding='utf-8'
        )
    else:
        fh = logging.FileHandler(name, encoding='utf-8')

    if level.upper() == 'TRACE':
        level = TRACE_LEVEL
    else:
        level = getattr(logging, level.upper(), None)
    if not isinstance(level, int):
        raise ValueError('Bad logging level')

    fh.setLevel(level)

    formatter = logging.Formatter(current_process_id + ' [%(threadName)s] %(asctime)s : %(levelname)s ::: %(message)s')

    fh.setFormatter(formatter)

    logger.addHandler(fh)

    logger.info('Logger created. Log file: ' + os.path.abspath(name))

    return logger


def init_console_log(level='DEBUG'):
    """
    Log initializer for standalone mode.
    :return:  logger
    """
    logger = logging.getLogger()
    add_log_level_trace(logger)
    logger.setLevel(0)  # take all in root

    ch = logging.StreamHandler()
    if level.upper() == 'TRACE':
        level = TRACE_LEVEL
    else:
        level = getattr(logging, level.upper(), None)
    if not isinstance(level, int):
        raise ValueError('Bad logging level')

    ch.setLevel(level)

    print('using raw console formatter')
    formatter_console = logging.Formatter(
        '[%(processName)s]  [%(threadName)s] %(asctime)s : %(levelname)s ::: %(message)s')

    ch.setFormatter(formatter_console)

    logger.addHandler(ch)
    logger.info('Console logger created.')

    return logger


def log_exception(e):
    """
    logs represenation of Exception + Traceback
    :param e:  Exception
    """
    logging.error(repr(e))
    tb = traceback.format_exc()
    logging.error(tb)
