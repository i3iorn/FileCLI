import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from file_handling.file import File
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, call_counter, \
    error_handler
from validator.exceptions import RuleException, ConditionException, ResultStatusException


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class ResultStatus(Enum):
    FAILURE = 0
    SUCCESS = 1
    ERROR = 2

    @classmethod
    def from_int(cls, number):
        try:
            if isinstance(number, str):
                if number.isnumeric():
                    number = int(number)
            if isinstance(number, float):
                number = round(number)
            if isinstance(number, int):
                return [rs for rs in cls if rs.value == number].pop(0)
        except Exception as e:
            raise ResultStatusException(f'Can not get {cls.__name__} from {number}') from e
        raise ResultStatusException(f'Can not get {cls.__name__} from {number}')


@dataclass
class ConditionResult:
    status: ResultStatus
    function: Callable
    score: float

    def __hash__(self):
        return hash(self.function)

    def __bool__(self):
        return self.status == ResultStatus.SUCCESS


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class Condition:
    log = logging.getLogger(__name__)

    def __init__(
            self,
            correct_value: Any,
            function: callable
    ):
        self.correct_value = correct_value
        self.function = function

    def evaluate(self, value: Any) -> ConditionResult:
        score = self.function(value)
        if not isinstance(score, float):
            raise ConditionException(f'Condition function needs to return a float')
        return ConditionResult(
            status=ResultStatus.from_int(score),
            function=self.function,
            score=score
        )

    def __hash__(self):
        return hash(self.function)

    def __eq__(self, other):
        return self.function == other.function and self.correct_value == other.value


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
def score_calc(old_score, new_score, weight):
    """
        Calculate the weighted score based on the old score, new score, and weight.

        Args:
        old_score (float): The old score.
        new_score (float): The new score.
        weight (float): The weight.

        Returns:
        float: The calculated score.
        """
    return old_score + ((new_score - old_score) * weight)


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class Rule:
    log = logging.getLogger(__name__)

    def __init__(
            self,
            score_formula: Callable = score_calc
    ):
        self.conditions = set()
        self.condition_results = set()
        self.score_formula = score_formula

    def add_condition(self, condition: Condition, weight: float = 1.0):
        if not issubclass(type(condition), Condition):
            raise RuleException(f'Can only add conditions to a rule, not {type(condition)}')
        try:
            self.conditions.add((condition, weight))
        except ValueError as e:
            raise RuleException(f'Could not add condition to rule.') from e

    def evaluate(self, value) -> float:
        score = 1.0
        for condition, weight in self.conditions:
            condition_result = condition.evaluate(value)
            self.condition_results.add(condition_result)
            score = self.score_formula(score, condition_result.score, weight)
        return score


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class Validator:
    def __init__(self):
        self.rules = set()
        self.results = []
        self.threshhold = 1.0

    def add_rule(self, rule: Rule):
        self.rules.add(rule)

    def validate(self, file: File) -> bool:
        for rule in self.rules:
            self.results.append(rule.evaluate(file))
        return min(self.results) > self.threshhold

    def prepare(self, file: File):
        raise NotImplementedError(f'Needs to be implemented in a subclass.')
