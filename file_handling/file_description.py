import csv
from dataclasses import dataclass


@dataclass
class Description:
    lineterminator: str = '\n'
    delimiter: str = ','
    quotechar: str = '"'
    quoting: int = 0,
    escapecharacter: str = None


CSV = Description()