import codecs
import csv
import logging
import chardet
from enum import Enum
from io import BytesIO
from time import sleep
from typing import TYPE_CHECKING

from custom_logging import logging_setup
from file_handling.exceptions import EncodingException
from helpers import get_data_type
from helpers.decorators import (class_decorator, log_method_calls, log_return_value, log_time, error_handler,
                                call_counter, input_type_validation)

if TYPE_CHECKING:
    from file_handling.file import File


class Delimiter(Enum):
    NONE = None
    COMMA = ","
    SEMICOLON = ";"
    TAB = "\t"
    SPACE = " "


class LineTerminator(Enum):
    CRLF = "\r\n"
    LF = "\n"
    CR = "\r"


class Quotechar(Enum):
    DOUBLE_QUOTE = '"'
    SINGLE_QUOTE = "'"
    BACKTICK = "`"
    NONE = ""


class Header(Enum):
    """
    Returns a boolean value for the header row. If the header row is present, the value is True. If the header row is
    not present, the value is False.
    """
    TRUE = True
    FALSE = False


class Encoding(Enum):
    ASCII = "ascii"
    ANSI = "ansi"
    ISO_8859_1 = "iso-8859-1"
    WINDOWS_1252 = "windows-1252"
    UTF_8_BOM = "utf-8-sig"
    UTF_8 = "utf-8"
    CP1252 = "cp1252"
    LATIN_1 = "latin_1"
    MACROMAN = "macroman"
    UTF_16_BE = "utf-16-be"
    UTF_16_LE = "utf-16-le"
    UTF_16 = "utf-16"
    UTF_32_BE = "utf-32-be"
    UTF_32_LE = "utf-32-le"
    UTF_32 = "utf-32"
    CP850 = "cp850"
    CP1250 = "cp1250"
    CP1251 = "cp1251"
    CP1253 = "cp1253"

    @classmethod
    def get(cls, encoding):
        """
        Get the encoding from the encoding string.
        """
        try:
            return getattr(Encoding, encoding.upper().replace("-", "_"))
        except:
            return None


class EnumDescriptor:
    def __init__(self, enum_class):
        self.enum_class = enum_class

    def __get__(self, instance, owner):
        return self.enum_class

    def __set__(self, instance, value):
        try:
            if not isinstance(value, self.enum_class):
                if isinstance(value, str):
                    try:
                        value = self.enum_class(value)
                    except ValueError:
                        pass
                raise ValueError(f"{value} is not a valid {self.enum_class.__name__.lower()}.")

            self.enum_class = value
        except TypeError as e:
            raise TypeError(f'{self.enum_class} is not a type, tuple, or union. Was used on {value}')

    def value(self):
        return self.enum_class.value

    def name(self):
        return self.enum_class.name


def sniffer_error_handler(cls, method, name, exception):
    """
    An error handler to handle exceptions raised by the FileSniffer class.

    :param cls: The class that raised the exception.
    :param exceptions: The exceptions raised by the class.
    :return: None
    """
    sleep(0.11)
    command = input(f"An error occurred in {name}. The error is {exception}. Press enter to continue, type "
                 f"'exit' to exit, or provide a value for {name}:")
    if command.lower() == 'exit':
        raise SystemExit
    if command:
        if command in ['True', 'False']:
            command = bool(command)
        setattr(cls, name, command)


@class_decorator(log_method_calls, log_return_value, log_time, error_handler, call_counter)
class FileSniffer:
    """
    A class to infer file characteristics from a delimited file. The file characteristics are encoding, delimiter,
    line terminator, quote character, and header. The class has a number of methods to infer the file characteristics
    from the file. The class also has a method to infer a file characteristic from the file. The method is named
    infer_file_characteristic and takes a file characteristic as an argument. The file characteristic is inferred by
    calling the infer method of the file characteristic. The infer method is named infer_{file_characteristic} where
    {file_characteristic} is the name of the file characteristic in lower case.

    The class has a constant BYTES_TO_ANALYZE that is used to determine the size of the sample of the file that is used
    to infer the file characteristics.
    """
    log = logging_setup(__name__)
    BYTES_TO_ANALYZE = 16184

    def __init__(self, file: "File", bytes: int = None):
        self.delimited_file = file
        self.sample = file.get_random_sample(self.BYTES_TO_ANALYZE)

        if hasattr(file, "_encoding"):
            self.log.debug(f"Sniffing encoding for {file.path}")
            self._encoding = self.infer_encoding()

        if hasattr(file, "_delimiter"):
            self.log.debug(f"Sniffing delimiter for {file.path}")
            self._line_terminator = self.infer_line_terminator()

        if hasattr(file, "_lineterminator"):
            self.log.debug(f"Sniffing line terminator for {file.path}")
            self._delimiter = self.infer_delimiter()

        if hasattr(file, "_quotechar"):
            self.log.debug(f"Sniffing quote character for {file.path}")
            self._quotechar = self.infer_quotechar()

        if hasattr(file, "_header"):
            self.log.debug(f"Sniffing header for {file.path}")
            self._header = self.infer_header()

        if bytes is not None:
            self.BYTES_TO_ANALYZE = bytes

    @property
    def encoding(self) -> Encoding:
        if not hasattr(self, "_encoding"):
            self.encoding = self.infer_encoding()
        return self._encoding

    @encoding.setter
    @input_type_validation(Encoding)
    def encoding(self, value: Encoding) -> None:
        self._encoding = value

    @property
    def delimiter(self) -> Delimiter:
        if not hasattr(self, "_delimiter"):
            self.delimiter = self.infer_delimiter()
        return self._delimiter

    @delimiter.setter
    @input_type_validation(Delimiter)
    def delimiter(self, value: Delimiter) -> None:
        self._delimiter = value

    @property
    def lineterminator(self) -> LineTerminator:
        if not hasattr(self, "_line_terminator"):
            self.lineterminator = self.infer_line_terminator()
        return self._lineterminator

    @lineterminator.setter
    @input_type_validation(LineTerminator)
    def lineterminator(self, value: LineTerminator) -> None:
        self._lineterminator = value

    @property
    def quotechar(self) -> Quotechar:
        if not hasattr(self, "_quotechar"):
            self.quotechar = self.infer_quotechar()
        return self._quotechar

    @quotechar.setter
    @input_type_validation(Quotechar)
    def quotechar(self, value: Quotechar) -> None:
        self._quotechar = value

    @property
    def header(self) -> Header:
        if not hasattr(self, "_header"):
            self.header = self.infer_header()
        return self._header

    @header.setter
    @input_type_validation(Header)
    def header(self, value: Header) -> None:
        self._header = value

    def infer_file_characteristic(self, fc):
        """
        Infer a file characteristic from the file. The file characteristic is inferred by calling the infer method of the
        file characteristic. The infer method is named infer_{file_characteristic} where {file_characteristic} is the
        name of the file characteristic in lower case.

        :param fc:
        :return:
        """
        try:
            return getattr(self, f"infer_{fc}")()
        except AttributeError:
            raise ValueError(f"{fc} is not a valid file characteristic.")

    def infer_encoding(self) -> Encoding:
        """
        Infer the encoding of the file by trying to decode the sample of the file with each encoding in the Encodings
        enumeration. If the sample can be decoded with an encoding, the encoding is assumed to be the encoding of the
        file. If the sample cannot be decoded with any encoding, an EncodingException is raised.

        :return:
        """
        for i in range(5):
            candidates = []
            for encoding in Encoding:
                try:
                    self.sample.decode(encoding.value)
                    candidates.append(encoding)
                except UnicodeDecodeError:
                    pass

            charset_value = chardet.detect(self.sample)['encoding']

            if Encoding.get(charset_value) in candidates:
                return Encoding.get(charset_value)

            self.sample = self.delimited_file.get_random_sample(self.BYTES_TO_ANALYZE * i)

        raise EncodingException("Could not infer encoding.")

    def infer_delimiter(self) -> Delimiter:
        """
        Infer the delimiter of the file by counting occurrences of each delimiter in a given sample of the file.

        :return: The delimiter of the file.
        """
        counts = {delim: self.sample.count(delim.value.encode()) for delim in Delimiter if delim != Delimiter.NONE}
        return max(counts, key=counts.get)

    def infer_line_terminator(self) -> LineTerminator:
        """
        Infer the line terminator of the file by counting occurrences of each line terminator in a given sample of the
        file. Takes into account that the line terminator might be a combination of \r and \n. The line terminator is
        assumed to be the one with the most occurrences. Unless the second most common line terminator is \r\n and the
        difference between the two is less than 10% of the total number of line terminators. In that case, the line
        terminator is assumed to be \r\n.

        :return: The line terminator of the file.
        """
        counts = {lt: self.sample.count(lt.value.encode()) for lt in LineTerminator}
        if counts[LineTerminator.CRLF] > counts[LineTerminator.LF] + counts[LineTerminator.CR] * 0.9:
            return LineTerminator.CRLF
        if counts[LineTerminator.LF] == counts[LineTerminator.CR]:
            return LineTerminator.CRLF
        return max(counts, key=counts.get)

    def infer_quotechar(self) -> Quotechar:
        """
        Infer the quote character of the file by using the csv.Sniffer to infer the quote character of the file.

        :return:
        """
        if self.encoding is None:
            self.encoding = self.infer_encoding()

        # Count the number of occurrences of each quote character in the sample
        counts = {qc: self.sample.count(qc.value.encode()) for qc in Quotechar if qc != Quotechar.NONE}

        # If the number of occurrences of each quote character is 0, the quote character is assumed to be none
        if all([count == 0 for count in counts.values()]):
            return Quotechar.NONE

        # If the number of occurrences of each quote character is not 0, the quote character is inferred by using the
        # csv.Sniffer to infer the quote character of the file.
        try:
            dialect = csv.Sniffer().sniff(
                sample=str(codecs.iterdecode(BytesIO(self.sample), self.encoding.value)),
                delimiters=self.delimiter.value
            )
            return Quotechar(dialect.quotechar)
        except csv.Error:
            return Quotechar.NONE

    def infer_header(self) -> Header:
        """
        Infers a header row by checking if the data type of the first row fields differ from the data type of the
        following row fields. If the data type of the first row fields differ from the data type of the following row
        fields, the first row is assumed to be a header row.

        :return:
        """
        # Create a CSV reader from the I/O stream
        if self.quotechar == Quotechar.NONE:
            options = {
                "delimiter": self.delimiter.value,
                "lineterminator": self.lineterminator.value
            }
        else:
            options = {
                "delimiter": self.delimiter.value,
                "lineterminator": self.lineterminator.value,
                "quotechar": self.quotechar.value,
                "quoting": csv.QUOTE_MINIMAL
            }

        reader = csv.reader(
            codecs.iterdecode(BytesIO(self.sample), self.encoding.value),
            **options
        )

        # Get the data type of the first row fields
        first_row_data_types = [get_data_type(field) for field in next(reader)]
        if not all([data_type == str for data_type in first_row_data_types]):
            return Header.FALSE

        # Check if the data type of the first row fields differ from the data type of the following rows fields

        checks = {
            line_num: {
                i: get_data_type(row[i])
                for i, field in enumerate(row)
            }
            for line_num, row in enumerate(reader)
        }

        # Check if more than 10% of the fields in the first row have a different data type than the fields in the
        # following rows. If so, the first row is assumed to be a header row.
        self.log.debug(first_row_data_types)
        first_row_type_length = len(first_row_data_types)

        diff = sum([1 for i in range(first_row_type_length) if first_row_data_types[i] != checks[0][i]]) / first_row_type_length
        if diff > 0.1:
            return Header.TRUE

        return Header.FALSE
