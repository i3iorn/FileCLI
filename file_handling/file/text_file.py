import os
from typing import Union

from custom_logging import logging_setup
from file_handling.analyze.sniffer import EnumDescriptor, LineTerminator, Encoding, Header, FileSniffer
from file_handling.file import File
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, call_counter, error_handler


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class TextFile(File):
    """
    The TextFile class is a subclass of the File class. The class provides methods to read and write text files.
    """
    log = logging_setup(__name__)
    lineterminator = EnumDescriptor(LineTerminator)
    encoding = EnumDescriptor(Encoding)
    header = EnumDescriptor(Header)

    def __init__(self, path_str: Union[str, os.PathLike], **options) -> None:
        super().__init__(path_str, **options)

    def content(self) -> str:
        """
        Read the file and return the content as a string.

        :return:
        """
        self.read()
