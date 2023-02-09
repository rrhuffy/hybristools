import atexit
import inspect
import logging
import os
import pickle
from functools import wraps

import sys
import zlib


def get_cache_filename_for_caller(postfix='cache', caller_depth=1):
    caller_file_path = inspect.stack()[caller_depth][1]
    return f'{caller_file_path}.{postfix}'


def load_object_from_file(file_path=None, default=None, compress=True):
    if file_path is None:
        file_path = get_cache_filename_for_caller(caller_depth=2)

    if not os.path.exists(file_path):
        return default

    with open(file_path, 'rb') as input_file:
        if compress:
            return pickle.loads(zlib.decompress(input_file.read()))
        else:
            return pickle.loads(input_file.read())


def save_object_to_file(object_to_put, file_path=None, compress=True):
    # use urllib.request.pathname2url when using user-provided part of filepath
    # for example regexes can't be saved as file
    if file_path is None:
        file_path = get_cache_filename_for_caller(caller_depth=2)

    with open(file_path, 'wb') as output_file:
        if compress:
            output_file.write(zlib.compress(pickle.dumps(object_to_put)))
        else:
            output_file.write(pickle.dumps(object_to_put))


def double_wrap(func):
    """
    # TODO: second option: https://realpython.com/primer-on-python-decorators/#both-please-but-never-mind-the-bread
    def name(_func=None, *, kw1=val1, kw2=val2, ...):  # 1
        def decorator_name(func):
            ...  # Create and return a wrapper function.

        if _func is None:
            return decorator_name                      # 2
        else:
            return decorator_name(_func)               # 3
    """

    # TODO: third option: https://github.com/dabeaz/python-cookbook/blob/master/src/9/defining_a_decorator_that_takes_an_optional_argument/example.py

    """
    https://stackoverflow.com/questions/653368/how-to-create-a-python-decorator-that-can-be-used-either-with-or-without-paramet
    a decorator decorator, allowing the decorator to be used as @decorator(with, arguments, and=kwargs) or @decorator
    """

    @wraps(func)
    def decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # actual decorated function
            return func(args[0])
        else:
            # decorator arguments
            return lambda real_function: func(real_function, *args, **kwargs)

    return decorator


# TODO: rename to volatile_kwargs
@double_wrap
def file_cache(func, volatile_arguments=None):
    # TODO: save results in RAM and eg. once per second flush to disk (use COW; separate file to save, then rename)
    # TODO: add default parameter: cache_validity_period_h=24
    # change dictionary 'cache' structure: [key, value] -> [key, [timestamp, value]]
    # check on every wrapper call if data from cache isn't older than cache_validity
    # for using arguments inside decorator:
    # https://blogs.it.ox.ac.uk/inapickle/2012/01/05/python-decorators-with-optional-arguments/

    # https://pythonhosted.org/joblib/memory.html
    # https://github.com/joblib/joblib
    # https://github.com/reubano/mezmorize
    # https://github.com/phizaz/jum
    # http://stackoverflow.com/questions/16463582/memoize-to-disk-python-persistent-memoization
    # https://github.com/garabik/stupydcache

    cache_file_path = get_cache_filename_for_caller(postfix=f'{func.__name__}.cache', caller_depth=3)
    if os.path.exists(cache_file_path):
        func.cache = load_object_from_file(cache_file_path)
    else:
        func.cache = {}

    original_func_cache = func.cache.copy()

    def save_cache_if_changed():
        if func.cache != original_func_cache:
            logging.debug(f'Saving new cache for {cache_file_path}')
            save_object_to_file(func.cache, cache_file_path)
        else:
            logging.debug(f'No changes in cache for {cache_file_path}')

    # WARNING: if using PyCharm then set "kill.windows.processes.softly=true" in:
    # C:\Program Files\JetBrains\PyCharm Community Edition 2019.1\bin\idea.properties
    # Otherwise killing program in middle of execution will prevent atexit from saving cached data to files
    # However it is still working if program will complete it's job and end normally without any exception
    atexit.register(save_cache_if_changed)

    @wraps(func)
    def wrapper(*args, **kwargs):
        if volatile_arguments is not None:
            assert isinstance(volatile_arguments, (list, tuple))
            kwargs_for_cache_key = {key: value for (key, value) in kwargs.items() if key not in volatile_arguments}
        else:
            # remain untouched
            kwargs_for_cache_key = kwargs

        full_signature = _get_signature_of_method(func, args, kwargs_for_cache_key)
        try:
            cached_result = func.cache[full_signature]
            logging.debug(f'Using cache for {full_signature}) from {cache_file_path}')
            return cached_result
        except KeyError:
            logging.debug(f'No cache for {full_signature} in {cache_file_path}, firing method...')
            result = func(*args, **kwargs)
            func.cache[full_signature] = result
            return result

    return wrapper


def _get_signature_of_method(func, args, kwargs):
    func_name = func.__name__
    comma_delimited_args_with_kwargs = _get_comma_delimited_args_with_kwargs(args, kwargs)
    full_signature = f'{func_name}({comma_delimited_args_with_kwargs})'
    return full_signature


def _get_comma_delimited_args_with_kwargs(args, kwargs):
    arguments = ', '.join([repr(arg) for arg in args])
    keyword_arguments = ', '.join([f'{key}={repr(value)}' for key, value in kwargs.items()])
    return ', '.join([arg for arg in [arguments, keyword_arguments] if arg])


def pause_with_enter_or_exit(message=None, callback_before_exit=None):
    if message:
        print(message, end=' ')

    try:
        input('[Press Enter to continue or CTRL+C to abort]')
    except KeyboardInterrupt:
        print('\nAborted', end='', flush=True)
        if callback_before_exit is not None:
            print(', cleaning up...')
            callback_before_exit()
        else:
            print()
        sys.exit(0)


def format_time(total_seconds):
    total_seconds = int(total_seconds)
    seconds = total_seconds % 60
    minutes = int(total_seconds % 3600 / 60)
    hours = int(total_seconds / 3600)
    if total_seconds < 60:  # 0-60s -> __s
        return f'{seconds}s'
    elif total_seconds < 3600:  # 0-60min -> __m:__s
        return f'{minutes}m{seconds}s'
    else:  # 60m+ -> __h:__m:__s
        return f'{hours}h:{minutes}m:{seconds}s'
