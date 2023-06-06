"""A subclass of pathlib.Path that adds extra functions, conversions, and automatic validation"""

from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pathvalidate import validate_filepath

if TYPE_CHECKING:
    import os
    from typing import Any, Optional, Self


# Python's Path implementation is a little bit unsuaul
# Using type(Path()) is required to subclass Path but it may break in the future
# See: https://newbedev.com/subclass-pathlib-path-fails
class ExtendedPath((type(Path()))):
    """A subclass of pathlib.Path that adds extra functions, conversions, and automatic validation.

    Path represents a filesystem path but unlike PurePath, also offers methods to do system calls on path objects.
    Depending on your system, instantiating a Path will return either a PosixPath or a WindowsPath object. You can also
    instantiate a PosixPath or WindowsPath directly, but cannot instantiate a WindowsPath on a POSIX system or vice
    versa."""

    # TypeErrors occur in __new__ so it needs to be where the type modifications take place
    def __new__(
        cls,
        *args: str | bytes | os.PathLike[str] | int | datetime | date | float,
        **kwargs: Any,
    ) -> Self:
        path_fragments = [cls._convert_to_path(partial_path) for partial_path in args]
        full_path = Path(*path_fragments)
        validate_filepath(full_path, platform="auto")
        return super().__new__(cls, *path_fragments)

    # Add extra instance variables used for caching
    def __init__(
        self,
        *_args: str | bytes | os.PathLike[str] | int | datetime | date | float,
    ) -> None:
        self.read_bytes_cached_value = None
        self.cached_content_value = None
        super().__init__()

    # When values are appended to a path the new path should be validated
    def __truediv__(self, key: str | bytes | os.PathLike[str] | int | datetime | date | float) -> Self:
        full_path = super().__truediv__(self._convert_to_path(key))
        validate_filepath(full_path, platform="auto")
        return full_path

    @classmethod
    def _convert_to_path(
        cls, value: str | bytes | os.PathLike[str] | int | datetime | date | float
    ) -> os.PathLike[str]:
        """Converts a string, bytes, os.PathLike, int, datetime, date or float to a Path object.

        Args:
            value (str | bytes | os.PathLike[str] | int | datetime | date | float): The value to convert to a Path
            object.

        Returns:
            os.PathLike[str]: The value converted to a Path object."""

        # Datetime is converted to a unix timestamp
        # Datetime needs to be checked before date because datetime is a subclass of date
        if isinstance(value, datetime):
            return Path(str(int(value.timestamp())))

        # When these are cast to a string the value is perfectly reasonable
        if isinstance(value, (date, float, int, str, bytes)):
            return Path(str(value))

        return value

    def aware_mtime(self) -> datetime:
        """Get the mtime of a file as a timezone aware datetime object

        Returns:
            datetime: The mtime of the file as a timezone aware datetime object"""

        return datetime.fromtimestamp(self.stat().st_mtime).astimezone()

    def up_to_date(self, timestamp: Optional[datetime] = None) -> bool:
        """Checks if the file is up to date with respect to a given timestamp.

        Args:
            timestamp (Optional[datetime], optional): A datetime that the file's mtime will be compared to. If no
            datetime is given th file will be checked for existance. Defaults to None.

        Returns:
            bool:
                True if the file exists and is up to date. False if the file does not exist or is outdated."""

        # If file does not exist it can't be up to date
        if not self.exists():
            return False

        # If no timestamp is given and the file exists it is up to date
        if timestamp is None:
            return True

        # When there is a file and a timestamp make the timestamp timezone aware and compare it to the file's mtime
        return self.aware_mtime() > timestamp.astimezone()

    def outdated(self, timestamp: Optional[datetime] = None) -> bool:
        """Checks if the file is outdated with respect to a given timestamp.

        Args:
            timestamp (Optional[datetime], optional): A datetime that the file's mtime will be compared to. If no
            datetime is given th file will be checked for existance. Defaults to None.
        Returns:
            bool: True if the file does not exist or is outdated. False if the file exists and is up to date."""

        return not self.up_to_date(timestamp)

    def write(self, content: bytes | str):
        """Write a bytes or a str object to a file, and will automatically create the directory if needed

        Args:
            content (bytes | str): The content to write to the file"""

        ExtendedPath(self.parent).mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            with self.open("wb") as file:
                file.write(content)  # Silly to have this listed twice, but it's required for Pylance
        else:
            with self.open("w", encoding="utf-8") as file:
                file.write(content)  # Silly to have this listed twice, but it's required for Pylance

    def delete(self):
        """Delete a folder or a file without having to worry about which it is This is useful because normally files and
        folders need to different commands to delete them. This function is a little bit dangerous because it can
        accidently delete a folder so it should be used with caution."""

        if self.exists():
            if self.is_file():
                self.unlink()
            else:
                shutil.rmtree(self)

    def read_text_cached(self, reload: bool = False, encoding: str = "utf-8"):
        """Read a file and cache the result to avoid reading the file multiple times

        Args:
            reload (bool, optional): If True, reload the file into the cache. Defaults to False.
            encoding (str, optional): Encoding to use to read the file. Defaults to "utf-8".

        Returns:
            _type_: The content of the file as a string"""

        if not self.cached_content_value or reload:
            self.cached_content_value = self.read_text(encoding=encoding)

        return self.cached_content_value

    def read_bytes_cached(self, reload: bool = False):
        """Read a file and cache the result to avoid reading the file multiple times

        Args:
            reload (bool, optional): If True, reload the file into the cache. Defaults to False.

        Returns:
            _type_: The content of the file as bytes"""

        if not self.read_bytes_cached_value or reload:
            self.read_bytes_cached_value = self.read_bytes()

        return self.read_bytes_cached_value
