from collections import Counter
from pathlib import Path
from enum import Enum

from custom_logging import logging_setup
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, error_handler, call_counter


class FileType(Enum):
    UNKNOWN = {
        'file_extension': '',
        'description': 'An unknown file type',
        'byte_signature': b'',
        'is_text': False
    }
    PDF = {
        'file_extension': '.pdf',
        'description': 'A PDF file',
        'byte_signature': b'%PDF',
        'is_text': False
    }
    EXCEL_LEGACY = {
        'file_extension': '.xls',
        'description': 'An Excel file',
        'byte_signature': b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',
        'is_text': False
    }
    EXCEL = {
        'file_extension': '.xlsx',
        'description': 'An Excel file',
        'byte_signature': b'\x50\x4b\x03\x04',
        'is_text': False
    }
    CSV = {
        'file_extension': '.csv',
        'description': 'A CSV file',
        'byte_signature': b'',
        'is_text': True,
        'delimiter': ','
    }
    JSON = {
        'file_extension': '.json',
        'description': 'A JSON file',
        'byte_signature': b'',
        'is_text': True
    }
    ZIP = {
        'file_extension': '.zip',
        'description': 'A ZIP file',
        'byte_signature': b'PK\x03\x04',
        'is_text': False
    }
    GZIP = {
        'file_extension': '.gz',
        'description': 'A GZIP file',
        'byte_signature': b'\x1f\x8b',
        'is_text': False
    }
    TAR = {
        'file_extension': '.tar',
        'description': 'A TAR file',
        'byte_signature': b'',
        'is_text': False
    }
    XML = {
        'file_extension': '.xml',
        'description': 'An XML file',
        'byte_signature': b'',
        'is_text': True
    }
    HTML = {
        'file_extension': '.html',
        'description': 'An HTML file',
        'byte_signature': b'',
        'is_text': True
    }
    TEXT = {
        'file_extension': '.txt',
        'description': 'A text file',
        'byte_signature': b'',
        'is_text': True
    }
    JSONL = {
        'file_extension': '.jsonl',
        'description': 'A JSON Lines file',
        'byte_signature': b'',
        'is_text': True
    }
    TSV = {
        'file_extension': '.tsv',
        'description': 'A TSV file',
        'byte_signature': b'',
        'is_text': True,
        'delimiter': '\t'
    }
    PIPE = {
        'file_extension': '.pipe',
        'description': 'A pipe-delimited file',
        'byte_signature': b'',
        'is_text': True,
        'delimiter': '|'
    }
    FIXED_WIDTH = {
        'file_extension': '.fixed_width',
        'description': 'A fixed width file',
        'byte_signature': b'',
        'is_text': True
    }
    NUMBERS = {
        'file_extension': '.numbers',
        'description': 'Mac Numbers file',
        'byte_signature': b'',
        'is_text': False
    }
    PAGES = {
        'file_extension': '.pages',
        'description': 'Mac Pages file',
        'byte_signature': b'',
        'is_text': False
    }

    @property
    def file_extension(self):
        return self.value['file_extension']

    @property
    def description(self):
        return self.value['description']

    @property
    def byte_signature(self):
        return self.value['byte_signature']

    @property
    def is_text(self):
        return self.value['is_text']

    @property
    def delimiter(self):
        if self.is_text:
            return self.value.get('delimiter', None)
        return None

    @classmethod
    def from_extension(cls, suffix):
        for ft in cls:
            if ft.file_extension == suffix:
                return ft
        return cls.UNKNOWN

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __get__(self, instance, owner):
        return self

    def __set__(self, instance, value):
        raise AttributeError("Cannot set a value to an enum.")

    def __call__(self, *args, **kwargs):
        return self

    def __eq__(self, other):
        if isinstance(other, FileType):
            return self.value == other.value
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


@class_decorator(log_method_calls, log_return_value, log_time, error_handler, call_counter)
class FileTypeAnalyzer:
    log = logging_setup(__name__)

    @classmethod
    def file_type(cls, file_path) -> FileType:
        """
        Returns the file type of a file based on extension, byte signature, and file characteristics.

        :param file_path: The path to the file.
        :return: The file type.
        """
        ft_from_extension = cls.file_type_from_extension(file_path)
        ft_from_signature = cls.file_type_from_signature(file_path)
        ft_from_characteristics = cls.file_type_from_characteristics(file_path)

        # If any two file types are the same, return that file type.
        if ft_from_extension == ft_from_signature and ft_from_extension != FileType.UNKNOWN:
            return ft_from_extension
        elif ft_from_extension == ft_from_characteristics and ft_from_extension != FileType.UNKNOWN:
            return ft_from_extension
        elif ft_from_signature == ft_from_characteristics and ft_from_signature != FileType.UNKNOWN:
            return ft_from_signature
        elif ft_from_signature != FileType.UNKNOWN:
            return ft_from_signature
        elif ft_from_extension is FileType.UNKNOWN and ft_from_characteristics == FileType.FIXED_WIDTH:
            return ft_from_characteristics
        elif ft_from_characteristics != FileType.UNKNOWN:
            return ft_from_characteristics

        return FileType.TEXT

    @classmethod
    def file_type_from_extension(cls, file_path: str) -> FileType:
        """
        Returns the file type based on the file extension.

        :param file_path: The path to the file.
        :return: The file type.
        """
        return FileType.from_extension(Path(file_path).suffix)

    @classmethod
    def file_type_from_signature(cls, file_path: str) -> FileType:
        """
        Returns the file type based on the byte signature.

        :param file_path: The path to the file.
        :return: The file type.
        """
        with open(file_path, "rb") as file:
            byte_signature = file.read(16)

        for ft in FileType:
            if byte_signature.startswith(ft.byte_signature) and ft.byte_signature != b"":
                return ft

        return FileType.UNKNOWN

    @classmethod
    def file_type_from_characteristics(cls, file_path: str) -> FileType:
        """
        Returns the file type based on the file characteristics.

        :param file_path: The path to the file.
        :return: The file type.
        """
        with open(file_path, "rb") as file:
            first_line = next(file)
            lines = [first_line]
            for i in range(20):
                try:
                    lines.append(next(file))
                except StopIteration:
                    if i < 3:
                        return FileType.UNKNOWN
                    break

        if first_line.startswith(b"PK"):
            return FileType.ZIP
        elif first_line.startswith(b"<?xml"):
            return FileType.XML
        elif first_line.startswith(b"{"):
            return FileType.JSON
        elif first_line.startswith(b"["):
            return FileType.JSONL
        elif first_line.startswith(b"ID"):
            return FileType.PDF

        delimiters = [",", "\t", "|", ";"]
        counts = Counter([c for c in first_line if chr(c) in delimiters])
        if counts != {}:
            delimiter_count = counts.most_common(1)[0][1]
            if delimiter_count > 1:
                delimiter = counts.most_common(1)[0][0]
                if delimiter == ord(","):
                    return FileType.CSV
                elif delimiter == ord("\t"):
                    return FileType.TSV
                elif delimiter == ord("|"):
                    return FileType.PIPE
                elif delimiter == ord(";"):
                    return FileType.CSV

        if len(Counter([len(line) for line in lines])) == 1:
            return FileType.FIXED_WIDTH

        return FileType.UNKNOWN