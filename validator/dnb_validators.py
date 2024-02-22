import logging

from validator import Validator
from validator.rules import SimpleHeader, UniformFields, CsvCharacteristics


class IqReport(Validator):
    log = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.add_rule(SimpleHeader())
        self.add_rule(UniformFields(200))
        self.add_rule(CsvCharacteristics())
