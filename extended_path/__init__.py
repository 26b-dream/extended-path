from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pathvalidate import validate_filepath

if TYPE_CHECKING:
    import os
    from datetime import date
    from typing import Optional, Self


class IllegalWindowsFilenameError(Exception):
    """Raised when a path is an illegal name on Windows"""


class IllegalLinuxFilenameError(Exception):
    """Raised when a file name is too long to be valid on Linux"""


# There's a weird issue where with Path when you try to make a subclass of it
# It's impossible to subclass Path and instead need to subclass the concrete implementation
# See: https://newbedev.com/subclass-pathlib-path-fails
class ExtendedPath((type(Path()))):
    @classmethod
    def _convert_to_path(cls, name: str | bytes | os.PathLike[str] | int | datetime | date | float) -> Path:
        # Datetime is converted to a unix timestamp
        # Datetime needs to be checked before date because datetime is a subclass of date
        if isinstance(name, datetime):
            name = int(name.timestamp())

        # date, int, and float can be safely converted to a string
        path_as_string = str(name)

        #  Windows, Mac & Linux all support /, for consistency only use this deliminator
        path_as_string = path_as_string.replace("\\", "/")

        path = Path(str(path_as_string))

        return path

    # TypeErrors occur in __new__ so it needs to be where the type modifications take place
    def __new__(
        cls,
        *args: str | bytes | os.PathLike[str] | int | datetime | date | float,
        **kwargs: str,
    ) -> Self:
        path_fragments = [cls._convert_to_path(partial_path) for partial_path in args]

        # Combine path fragments into a single path
        full_path = Path(*path_fragments)

        validate_filepath(full_path)

        return super().__new__(cls, *path_fragments)

    def __truediv__(self, key: str | bytes | os.PathLike[str] | int | datetime | date | float) -> Self:
        full_path = super().__truediv__(self._convert_to_path(key))
        validate_filepath(full_path)
        return full_path

    def up_to_date(self, timestamp: Optional[datetime] = None) -> bool:
        """Check if a file exists and is up to date"""

        # If file does not exist it can't be up to date
        if not self.exists():
            return False

        # If no timestamp is given and the file exists it is up to date
        if timestamp is None:
            return True

        # Make timestamp time zone aware for more relaible results
        timestamp = timestamp.astimezone()

        # If the file exists and there is a timestamp return the result of the comparison
        return self.aware_mtime() > timestamp

    def aware_mtime(self) -> datetime:
        """Get the last modified time of a file as a timezone aware datetime object"""

        return datetime.fromtimestamp(self.stat().st_mtime).astimezone()

    def outdated(self, timestamp: Optional[datetime] = None) -> bool:
        """Check if a file does not exist or is outdated"""
        return not self.up_to_date(timestamp)

    def write(self, content: bytes | str):
        """Write a bytes or a str object to a file, and will automatically create the directory if needed

        This is useful because str and byte objects need to be written to files with different parameters
        """

        ExtendedPath(self.parent).mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            with self.open("wb") as f:
                f.write(content)  # Silly to have this listed twice, but it's required for Pylance
        else:
            with self.open("w", encoding="utf-8") as f:
                f.write(content)  # Silly to have this listed twice, but it's required for Pylance

    def delete(self):
        """Delete a folder or a file without having to worry about which it is\n

        This is useful because normally files and folders need to be deleted differently
        """

        if self.exists():
            if self.is_file():
                self.unlink()
            else:
                shutil.rmtree(self)

    def read_text_cached(self, reload: bool = False):
        """Read a file and cache the result to avoid reading the file multiple times"""

        if not hasattr(self, "cached_content_value") or reload:
            self.cached_content_value = self.read_text()

        return self.cached_content_value

    def read_bytes_cached(self, reload: bool = False):
        """Read a file and cache the result to avoid reading the file multiple times"""

        if not hasattr(self, "read_bytes_cached_value") or reload:
            self.read_bytes_cached_value = self.read_bytes()

        return self.read_bytes_cached_value
