import functools
import logging
import sys
import traceback
from time import sleep


class InvalidResponseError(Exception):
    def __init__(self, message):
        super().__init__(message)


class MaxRetriesError(Exception):
    def __init__(self, message):
        super().__init__(message)


def retries_on(num=1, sleep_time_seconds=1):
    def decorator_retries(func):

        @functools.wraps(func)
        def wrapper_retries(*args, **kwargs):
            for i in range(num):
                try:

                    value = func(*args, **kwargs)
                    return value

                except Exception:

                    logging.info(f'Failed attempt {i + 1} while executing "{func.__name__}"')

                    traceback_formatted = '\n'.join(traceback.format_exception(*sys.exc_info()))
                    logging.debug(f'Error traceback: \n {traceback_formatted}')

                    if i + 2 > num:
                        raise MaxRetriesError(f'Max retries reached for "{func.__name__}"').with_traceback(
                            sys.exc_info()[2])

                    logging.info(f'Retry {i + 2} for "{func.__name__}"')
                    sleep(sleep_time_seconds)

        return wrapper_retries

    return decorator_retries
