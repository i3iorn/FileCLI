import csv
import logging
import os
import time
from pathlib import Path
from typing import Union, List

from custom_logging import logging_setup
from file_handling.file.text_file import TextFile
from file_handling.file_description import Description
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, call_counter, \
    error_handler, cache
from file_handling.analyze.sniffer import FileSniffer, EnumDescriptor, Encoding, Delimiter, LineTerminator, Quotechar


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class DelimitedFile(TextFile):
    """
    A class to represent a delimited file. The purpose is to infer and automate as much as possible the process of
    reading, analyzing, and writing delimited files. The class has a number of file characteristics that can be
    inferred from the file. The class also has a number of methods to change the file characteristics and to export the
    file to a new file with different file characteristics.
    """
    log = logging_setup(__name__)
    delimiter = EnumDescriptor(Delimiter)
    quotechar = EnumDescriptor(Quotechar)
    quoting = 0
    disable_call_counter = ['__repr__', '__str__']

    def __init__(self, path_str: Union[str, os.PathLike], **options) -> None:
        super().__init__(path_str, **options)
        self._data = options.get("data", None)

        start = time.perf_counter()
        for fc in ["header", "delimiter", "lineterminator", "quotechar", "encoding"]:
            if fc not in options:
                try:
                    setattr(self, fc, getattr(self._sniffer, fc))
                except TypeError as e:
                    if getattr(self._sniffer, fc) is None:
                        self.log.warning(f"File characteristic {fc} is not set.")
                    else:
                        raise e
        self.log.log(min(round((time.perf_counter()-start)*10), 50),f'Filesniffer took {time.perf_counter() - start}')

    @property
    def data(self) -> List[List[str]]:
        """
        Read the file and return the data as a list of lists. Each list represents a row in the file and each element in
        the list represents a field in the row.

        :return:
        """
        if self._data is not None:
            for row in self._data:
                yield row
        else:
            with open(self.path, "r", encoding=self.encoding.value) as file:
                if self.quotechar == Quotechar.NONE:
                    reader = csv.reader(file, delimiter=self.delimiter.value, lineterminator=self.lineterminator.value)
                else:
                    reader = csv.reader(file, delimiter=self.delimiter.value, quotechar=self.quotechar.value,
                                        lineterminator=self.lineterminator.value, quoting=csv.QUOTE_MINIMAL)
                for row in reader:
                    yield row

    def filter_data(self, condition_func: callable) -> List[List[str]]:
        """
        Filter rows based on the provided condition function.

        :param condition_func: A callable function that takes a row (list of strings) as input and returns a boolean.
        :return: A list of rows that satisfy the condition.
        """
        for row in self.data:
            if condition_func(row):
                yield row

    @cache
    def __len__(self) -> int:
        """
        Return the number of rows in the file.

        :return:
        """
        return sum(1 for _ in self.data)

    def __getitem__(self, item: int) -> List[str]:
        """
        Get a specific row in the file.

        :param item: The index of the row.
        :return:
        """
        data = list(self.data)
        return data[item]

    def __iter__(self) -> List[List[str]]:
        """
        Return an iterator for the file.

        :return:
        """
        return self.data

    def __next__(self) -> List[str]:
        """
        Get the next row in the file.

        :return:
        """
        return next(self.data)

    def merge(self, other: "DelimitedFile") -> "DelimitedFile":
        """
        Merge the file with another file on a specific column.

        :param other: The other file to merge with.
        :param on: The column to merge on.
        :return: A new DelimitedFile instance with the merged data.
        """
        data = []
        for row in self.data:
            data.append(row)
        for row in other.data:
            data.append(row)
        return DelimitedFile(data=data)

    @classmethod
    def from_data_list(cls, data: List[List[str]], header) -> "DelimitedFile":
        """
        Create a new DelimitedFile instance from a list of lists.

        :param data: The list of lists to create the DelimitedFile instance from.
        :return: A new DelimitedFile instance with the provided data.
        """
        return cls(
            path_str=Path("data.csv"),
            data=data,
            delimiter=Delimiter.COMMA,
            line_terminator=LineTerminator.LF,
            quotechar=Quotechar.DOUBLE_QUOTE,
            encoding=Encoding.UTF_8,
            header=header
        )

    def export(self, file_description: Description):
        options = {k: v for k, v in file_description.__dict__.items() if
                   not k.startswith('_') and v is not None}
        if 'quoting' in options.keys() and isinstance(options['quoting'], tuple):
            options['quoting'] = options['quoting'][0]
        with self as reader, open(self.path.with_suffix('.export'), 'w', encoding='utf-8-sig', errors='skip') as writer:
            csv_writer = csv.writer(writer, **options)
            for row in reader:
                csv_writer.writerow(row)
