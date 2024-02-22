from typing import List

from file_handling.file import File
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, call_counter, \
    error_handler
from validator import Condition
from validator.exceptions import ConditionException


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class HeaderContains(Condition):
    def __init__(self, names: list):
        super().__init__(
            names,
            self._look_for_names
        )

    def _look_for_names(self, header_row: str):
        return 1.0 if all(title in header_row for title in self.correct_value) else 0.0


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class HasHeader(Condition):
    def __init__(self, value: bool):
        super().__init__(
            value,
            self._check_for_header
        )

    def _check_for_header(self, file: File) -> float:
        if not isinstance(file, File):
            raise ConditionException(f'You can only check for header in subclasses of {File}')

        return 0.0


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class FieldLength(Condition):
    def __init__(self, field_length: int):
        if not isinstance(field_length, int) or field_length <= 0:
            raise ConditionException(f'Field length has to be and integer greater that zero')
        super().__init__(
            field_length,
            self._check_field_lengths
        )

    def _check_field_lengths(self, value: List[List[str]]):
        for row in value:
            for field in row:
                if len(field) > self.correct_value:
                    return 0.0
        return 1.0


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class RegularLineLength(Condition):
    def __init__(self, value: bool):
        if not isinstance(value, bool):
            raise ConditionException(f'Correct value has to be a boolean')
        super().__init__(
            value,
            self._check_field_lengths
        )

    def _check_field_lengths(self, value_list: List):
        lengths = set()
        for item in value_list:
            lengths.add(len(item))
        return 1.0 if bool(len(lengths) == 1) == self.correct_value else 0.0


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class FileProperty(Condition):
    def __init__(self, value: dict):
        if not isinstance(value, dict):
            raise ConditionException(f'Correct value has to be a dictionary')
        super().__init__(
            value,
            self._run_condition
        )

    def _run_condition(self, file: File):
        for attr, value in self.correct_value.items():
            if getattr(file, attr) != value:
                return 0.0
        return 1.0
