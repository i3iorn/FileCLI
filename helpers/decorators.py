import math
import time
from time import perf_counter


def log_method_calls(method, name, **callbacks):
    """
    A decorator to log method calls. The decorator logs the method name, the method arguments, and the method keyword
    arguments.

    :param name:
    :param method: The method to be decorated.
    :return: The decorated method.
    """

    def wrapper(self, *args, **kwargs):
        """
        A wrapper to log method calls. The wrapper logs the method name, the method arguments, and the method keyword
        arguments.

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        self.log.debug(f"Calling {name} with args: {args} and kwargs: {kwargs} from {self.__class__.__name__}, "
                       f"line {method.__code__.co_firstlineno}")
        return method(self, *args, **kwargs)

    return wrapper


def log_return_value(method, name, **callbacks):
    """
    A decorator to log the return value of a method. The decorator logs the method name and the return value.

    :param name:
    :param method: The method to be decorated.
    :return: The decorated method.
    """

    def wrapper(self, *args, **kwargs):
        """
        A wrapper to log the return value of a method. The wrapper logs the method name and the return value.

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        return_value = method(self, *args, **kwargs)
        self.log.debug(f"{name} returned {return_value[:200] if len(str(return_value) or []) > 200 else return_value}...")
        return return_value

    return wrapper


def log_time(method, name, **callbacks):
    """
    A decorator to log the execution time of a method. The decorator logs the method name and the execution time.

    :param name:
    :param method: The method to be decorated.
    :return: The decorated method.
    """

    def wrapper(self, *args, **kwargs):
        """
        A wrapper to log the execution time of a method. The wrapper logs the method name and the execution time.

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        start = perf_counter()
        return_value = method(self, *args, **kwargs)
        end = perf_counter()
        level = 1,
        limits = [0, 0.5, 2.5, 12.5, 60]
        levels = [10, 20, 30, 40, 50]
        while limits and end - start > limits.pop(0):
            level = levels.pop(0)

        self.log.log(level, f"{name} took {end - start:.5f} seconds to execute.")
        return return_value
    return wrapper


def error_handler(method, name, **callbacks):
    """
    A decorator to handle exceptions in a method. The decorator logs the exception and returns None.

    :param callbacks: Optional callbacks to be called after the method is executed.
    :param name: The name of the method.
    :param method: The method to be decorated.
    :return: The decorated method.
    """

    def wrapper(self, *args, **kwargs):
        """
        A wrapper to handle exceptions in a method. The wrapper logs the exception and returns None.

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            self.log.error(f"An error occurred in {name}: {e}")
            if 'on_error' in callbacks:
                callbacks['on_error'](self, method, name, e)
            else:
                self.log.debug(f"No error handler provided for {name}.")
                raise e
    return wrapper


def call_counter(method, name, **callbacks):
    """
    A decorator to count the number of times a method is called. The decorator logs the method name and the number of
    times the method is called.

    :param name: The name of the method.
    :param method: The method to be decorated.
    :return: The decorated method.
    """
    def wrapper(self, *args, **kwargs):
        """
        A wrapper to count the number of times a method is called. The wrapper logs the method name and the number of
        times the method is called.

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        if hasattr(self, 'disable_call_counter') and name in self.disable_call_counter:
            return method(self, *args, **kwargs)

        limits = [1, 10, 50, 250, 1000]
        levels = [10, 20, 30, 40, 50]

        if not hasattr(self, 'call_count'):
            self.call_count = {}
        if name not in self.call_count:
            self.call_count[name] = 0
        self.call_count[name] += 1

        level = 1
        while limits and self.call_count[name] > limits.pop(0):
            level = levels.pop(0)

        if level != 1 and (self.call_count[name] % 10 == 0 or level == 50 or self.call_count[name] < 10):
            self.log.log(level, f"{name} has been called {self.call_count[name]} times.")

        if level == 50:
            raise RecursionError(f"{name} has been called {self.call_count[name]} times.")

        return method(self, *args, **kwargs)
    return wrapper


def class_decorator(*decorators, **callbacks):
    """
    A decorator to decorate all methods of a class with a list of decorators.

    :param callbacks: Optional callbacks to be called after the class is decorated.
    :param decorators: The decorators to be applied to the methods of the class.
    :return:
    """
    def decorate(cls):
        if 'on_decorate' in callbacks:
            callbacks['on_decorate'](cls, decorators)
        for name, method in cls.__dict__.items():
            if not name.startswith('__') and not name.endswith('__'):
                if callable(method):
                    for decorator in decorators:
                        method = decorator(method, name, **callbacks)
                    setattr(cls, name, method)
        return cls
    return decorate


def retry(retries=3, delay=0):
    """
    A decorator to retry a method. The decorator retries the method a number of times and with a delay between retries.

    :param retries: The number of retries.
    :param delay: The delay between retries.
    :return: The decorated method.
    """

    def decorator(method):
        """
        A decorator to retry a method. The decorator retries the method a number of times and with a delay between
        retries.

        :param method: The method to be decorated.
        :return: The decorated method.
        """

        def wrapper(self, *args, **kwargs):
            """
            A wrapper to retry a method. The wrapper retries the method a number of times and with a delay between
            retries.

            :param self:
            :param args:
            :param kwargs:
            :return:
            """
            for _ in range(retries):
                try:
                    return method(self, *args, **kwargs)
                except Exception as e:
                    self.log.error(f"An error occurred in {method.__name__}: {e}")
                    self.log.debug(f"Retrying {method.__name__} in {delay} seconds")
                    self.sleep(delay)
            return None
        return wrapper
    return decorator


def cache(method):
    """
    A decorator to cache the return value of a method. The decorator caches the return value of the method in a dictionary
    with the method name as the key.

    :param method: The method to be decorated.
    :return: The decorated method.
    """

    def wrapper(self, *args, **kwargs):
        """
        A wrapper to cache the return value of a method. The wrapper caches the return value of the method in a dictionary
        with the method name as the key.

        :param self:
        :param args:
        :param kwargs:
        :return:
        """
        if kwargs.pop('DISABLE_CACHE', False):
            return method(self, *args, **kwargs)

        if not hasattr(self, 'cache'):
            self.cache = {}
        if method.__name__ not in self.cache:
            self.cache[method.__name__] = {
                'return_value': method(self, *args, **kwargs),
                'time': time.time()
            }
        elif time.time() - self.cache[method.__name__]['time'] > 60:
            self.cache[method.__name__] = {
                'return_value': method(self, *args, **kwargs),
                'time': time.time()
            }
        return self.cache[method.__name__]['return_value']
    return wrapper


def input_type_validation(*types):
    """
    A decorator to validate the input type of a method. The decorator validates the input type of the method and raises a
    TypeError if the input type is not valid.

    Can handle:
    - str
    - int
    - float
    - datetime
    - bool
    - list
    - tuple
    - dict
    - set
    - frozenset
    - bytes
    - bytearray
    - memoryview
    - range
    - complex
    - None
    - Any
    - Union
    - Optional
    - Literal
    - Type
    - AnyStr
    - SupportsInt
    - SupportsFloat
    - SupportsComplex
    - SupportsBytes
    - SupportsIndex
    - SupportsAbs
    - SupportsRound
    - SupportsBytes
    - SupportsComplex
    - Path
    - Pattern
    - Match
    - IO
    - AnyIO
    - BinaryIO
    - TextIO
    - Pathlike

    :param types: The types to be validated.
    :return: The decorated method.
    """
    def decorator(method):
        """
        A decorator to validate the input type of a method. The decorator validates the input type of the method and
        raises a TypeError if the input type is not valid.

        :param method: The method to be decorated.
        :return: The decorated method.
        """

        def wrapper(self, *args, **kwargs):
            """
            A wrapper to validate the input type of a method. The wrapper validates the input type of the method and
            raises a TypeError if the input type is not valid.

            :param self:
            :param args:
            :param kwargs:
            :return:
            """
            for arg, type_ in zip(args, types):
                if not isinstance(arg, type_):
                    raise TypeError(f"{arg} is not a valid {type_}.")
            for key, value in kwargs.items():
                if not isinstance(value, types[0]):
                    raise TypeError(f"{key} must be a {types[0]}.")
            return method(self, *args, **kwargs)
        return wrapper
    return decorator