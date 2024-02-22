import csv

from file_handling.analyze.sniffer import Delimiter, LineTerminator, Quotechar
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, call_counter, \
    error_handler
from validator import Rule
from validator.conditions import HasHeader, FieldLength, RegularLineLength, FileProperty


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class SimpleHeader(Rule):
    def __init__(self):
        super().__init__()
        self.add_condition(HasHeader(True), 0.1)


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class UniformFields(Rule):
    def __init__(self, field_length: int = 255, uniform_rows: bool = True):
        super().__init__()
        self.add_condition(FieldLength(field_length))
        self.add_condition(RegularLineLength(uniform_rows))


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class FileCharacteristics(Rule):
    def __init__(self, **options):
        super().__init__()
        self.add_condition(FileProperty(options))


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class CsvCharacteristics(Rule):
    def __init__(self, **options):
        super().__init__()
        defaults = {
            'extension': '.csv',
            'delimiter': Delimiter.COMMA,
            'lineterminator': LineTerminator.LF,
            'quoting': csv.QUOTE_MINIMAL,
            'quotechar': Quotechar.DOUBLE_QUOTE
        }
        defaults.update(options)
        self.add_condition(FileProperty(defaults))
