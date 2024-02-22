import hashlib
import logging
import os
import random
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Type, Union, Any, Generator

from custom_logging import logging_setup
from file_handling.analyze.sniffer import FileSniffer
from file_handling.exceptions import PathException, SampleException, BackupException
from helpers.decorators import class_decorator, log_method_calls, log_return_value, log_time, call_counter, \
    error_handler, cache


@class_decorator(log_method_calls, log_return_value, log_time, call_counter, error_handler)
class File:
    """
    A class to handle file operations. The class provides methods to create a backup of a file, restore a backup, and
    read a number of bytes from a file. The class also serves as a context manager to ensure that the backup is restored
    if an error occurs during file operations.
    """
    log = logging_setup(__name__)

    def __init__(self, path_str: Union[str, os.PathLike], **options) -> None:
        self._path = Path(path_str)
        self._sniffer = FileSniffer(self)
        for option, value in options.items():
            setattr(self, option, value)

    @property
    def extension(self) -> str:
        return self.path.suffix

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, value: Path) -> None:
        if not isinstance(value, Path):
            raise PathException(f"{value} is not a valid path.")
        self._path = value

    @property
    def sample(self) -> bytes:
        return self._sample

    @sample.setter
    def sample(self, value: bytes) -> None:
        if not isinstance(value, bytes):
            raise SampleException(f"{value} is not a valid sample.")
        if len(value) < 1:
            raise SampleException("The sample must contain at least one byte.")
        self._sample = value

    @property
    def backup(self) -> Path:
        return self._backup

    @backup.setter
    def backup(self, value: Path) -> None:
        if not isinstance(value, Path):
            raise BackupException(f"{value} is not a valid backup.")
        self._backup = value

    def __enter__(self) -> 'File':
        """
        Enter the context manager. The method creates a backup of the file and returns the instance.

        :return:
        """
        self.backup = self.backup_file()
        return self

    def __exit__(self, exc_type: Type[BaseException], exc_val: Union[None, BaseException], exc_tb: Any) -> bool:
        """
        Exit the context manager. The method logs any exception that occurred during the execution of the with block.
        If an exception occurred, the backup is restored. If no exception occurred, the backup is deleted.

        :param exc_type: The exception type.
        :param exc_val: The exception value.
        :param exc_tb: The exception traceback.
        :return:
        """
        if exc_type:
            self.log_error(exc_type, exc_val, exc_tb)
            self.restore_backup()
            return False
        self.backup.unlink(missing_ok=True)
        return True

    @cache
    def get_sample(self, bytes_to_read: int) -> bytes:
        """
        Get a sample of bytes from the file.

        :param bytes_to_read: The number of bytes to read.
        :return: The sample of bytes from the file.
        """
        return b"".join(self.read(bytes_to_read))

    @cache
    def get_random_sample(self, bytes_to_read: int) -> bytes:
        """
        Get a random set of chunks from the file.
        """
        try:
            with open(self.path, "rb") as file:
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                if file_size < bytes_to_read:
                    bytes_to_read = file_size

                chunk_size = 4096
                chunk_count = bytes_to_read // chunk_size

                random_chunks = []
                for _ in range(chunk_count):
                    random_position = random.randint(0, file_size - chunk_size)
                    file.seek(random_position)
                    random_chunks.append(file.read(chunk_size))

                return b"".join(random_chunks)
        except Exception as e:
            self.log_error(e.__class__, e, None)
            raise IOError(f"Error reading file: {e}")

    def backup_file(self) -> Path:
        """
        Create a backup of the file.

        :return: The path to the backup file.
        """
        try:
            backup_path = self.path.with_suffix(".bak")
            with open(self.path, "rb") as source, open(backup_path, "wb") as target:
                buffer_size = 4096  # Define a buffer size for efficient I/O
                while True:
                    # Read data from the original file in chunks
                    chunk = source.read(buffer_size)
                    if not chunk:
                        # If no more data is available, break the loop
                        break
                    # Write the read chunk to the backup file
                    target.write(chunk)
            return backup_path
        except Exception as e:
            # Handle any errors that occur during backup creation
            self.log_error(e.__class__, e, None)
            raise IOError(f"Error creating backup: {e}")

    def restore_backup(self) -> None:
        """
        Restore the backup of the file.

        :return: None
        """
        try:
            backup_path = self.backup
            with open(backup_path, "rb") as source, open(self.path, "wb") as target:
                buffer_size = 4096  # Define a buffer size for efficient I/O
                while True:
                    # Read data from the backup file in chunks
                    chunk = source.read(buffer_size)
                    if not chunk:
                        # If no more data is available, break the loop
                        break
                    # Write the read chunk to the original file
                    target.write(chunk)
        except Exception as e:
            # Handle any errors that occur during file restoration
            self.log_error(e.__class__, e, None)
            raise IOError(f"Error restoring backup: {e}")

    def log_error(self, exc_type: Type[BaseException], exc_val: Union[None, BaseException], exc_tb: Any) -> None:
        """
        Log an error with detailed information about its context.

        :param exc_type: The exception type.
        :param exc_val: The exception value.
        :param exc_tb: The exception traceback.
        :return: None
        """
        error_message = f"An error occurred: {exc_type.__name__}"

        # If the exception value is provided, include it in the error message
        if exc_val is not None:
            error_message += f": {exc_val}"

        # If the exception traceback is provided, include it in the debug log
        if exc_tb is not None:
            exc_tb_str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            self.log.debug(f"Traceback:\n{exc_tb_str}")

        # Log the error message at the error level
        self.log.error(error_message)

    @cache
    def read(self, bytes_to_read: int = None, lazy_read: bool = True, buffer_size: int = 4096, encoding: str = None,
             progress_callback=None, num_threads: int = 4, timeout: float = None
             ) -> Union[Generator[bytes, None, None], bytes, str]:
        """
        Read a number of bytes from the file.

        :param bytes_to_read: The number of bytes to read.
        :param lazy_read: A flag to indicate whether to read the file lazily.
        :param buffer_size: The size of the buffer to use for reading the file.
        :param encoding: The encoding to use for text file reading.
        :param progress_callback: An optional callback function to track the progress of the file reading operation.
        :param num_threads: The number of threads to use for parallel processing.
        :param timeout: The maximum time to wait for thread completion (in seconds).
        :return: The bytes read from the file.
        """
        if bytes_to_read is None:
            bytes_to_read = os.path.getsize(self.path)

        if bytes_to_read < 0:
            raise ValueError("bytes_to_read must be a non-negative integer.")

        if buffer_size <= 0:
            raise ValueError("buffer_size must be a positive integer.")

        if num_threads <= 0:
            raise ValueError("num_threads must be a positive integer.")

        # Dynamically adjust chunk size based on the number of threads and file size
        chunk_size = max(1, bytes_to_read // (num_threads * 2))
        remaining_bytes = bytes_to_read

        data_lock = threading.Lock()
        data = bytearray() if not lazy_read else None

        def read_chunk(file, chunk_start, chunk_size):
            try:
                file.seek(chunk_start)
                chunk = file.read(chunk_size)
                return chunk_start, chunk
            except Exception as e:
                return chunk_start, None, e

        try:
            with open(self.path, "rb") as file:
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    futures = []
                    for chunk_start in range(0, bytes_to_read, chunk_size):
                        future = executor.submit(read_chunk, file, chunk_start, chunk_size)
                        futures.append(future)

                    for future in as_completed(futures, timeout=timeout):
                        try:
                            chunk_start, chunk = future.result()
                            if len(future.result()) > 2:
                                raise future.result()[2]

                            if chunk:
                                with data_lock:
                                    if lazy_read:
                                        if progress_callback:
                                            progress_callback(chunk_start, bytes_to_read)
                                        yield chunk
                                    else:
                                        data.extend(chunk)
                                        if progress_callback:
                                            progress_callback(chunk_start, bytes_to_read)
                        except TimeoutError:
                            self.log_error(TimeoutError, TimeoutError("Thread timed out while reading chunks."), None)
                            raise IOError("Thread timed out while reading chunks.")

        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {self.path}") from e
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {self.path}") from e
        except KeyboardInterrupt:
            raise KeyboardInterrupt("File reading interrupted by user.")
        except Exception as e:
            self.log_error(e.__class__, e, None)
            raise IOError(f"Error reading file: {e}")

        if not lazy_read:
            if encoding:
                return data.decode(encoding)
            else:
                return bytes(data)

    def calculate_checksum(self, algorithm: str = 'sha256') -> str:
        """
        Calculate the checksum of the file's contents.

        :param algorithm: The hashing algorithm to use (e.g., 'md5', 'sha1', 'sha256').
        :return: The checksum of the file's contents.
        """
        try:
            hasher = hashlib.new(algorithm)
            with open(self.path, "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            self.log_error(e.__class__, e, None)
            raise IOError(f"Error calculating checksum: {e}")

    def __eq__(self, other: 'File') -> bool:
        """
        Compare the file to another file based on their paths.

        :param other: The other file.
        :return: True if the files have the same path, False otherwise.
        """
        if not isinstance(other, File):
            return False
        return self.calculate_checksum() == other.calculate_checksum()

    def __ne__(self, other: 'File') -> bool:
        """
        Determine inequality between files.

        :param other: The other file.
        :return: True if the files are not equal, False otherwise.
        """
        return not self.__eq__(other)

    def __str__(self) -> str:
        """
        Get a string representation of the file.

        :return: The string representation of the file.
        """
        return str(self.path)

    def __repr__(self) -> str:
        """
        Get a representation of the file.

        :return: The representation of the file.
        """
        return f"{self.__class__.__name__}({self.path})"
