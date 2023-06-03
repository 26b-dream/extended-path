from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

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
    ILLEGAL_STRINGS = (
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    )

    ILLEGAL_CHARACTERS = (
        "<",
        ">",
        ":",
        '"',
        "/",
        "\\",
        "|",
        "?",
        "*",
    )

    @classmethod
    def __convert_to_string(cls, name: str | bytes | os.PathLike[str] | int | datetime | date | float) -> Path:
        # Datetime is converted to a unix timestamp
        # Datetime needs to be checked before date because datetime is a subclass of date
        if isinstance(name, datetime):
            name = int(name.timestamp())

        # date, int, and float can be safely converted to a string
        path = Path(str(name))

        cls.__validate_path_fragment(path)

        return path

    @classmethod
    def __validate_path_fragment(cls, path_object: Path) -> None:
        """Validates a path fragment to ensure it is a valid file name on Windows and Linux"""

        # Just a period should never be valid because it is redundant
        if str(path_object) == ".":
            raise IllegalWindowsFilenameError(f'"{path_object}" is an illegal name on Windows')

        for path_fragement in path_object.parts:
            file_stem = Path(path_fragement).stem

            if path_fragement in cls.ILLEGAL_STRINGS or file_stem in cls.ILLEGAL_STRINGS:
                raise IllegalWindowsFilenameError(f'"{path_object}" is an illegal name on Windows')
            elif path_fragement.endswith("."):
                raise IllegalWindowsFilenameError(f'"{path_object}" path segment cannot end with a period on Windows')
            elif path_fragement.endswith(" "):
                raise IllegalWindowsFilenameError(f'"{path_object}" path cannot segment end with a space on Windows')
            elif path_fragement.endswith(" "):
                raise IllegalWindowsFilenameError(f'"{path_object}" path cannot segment end with a space on Windows')
            elif path_fragement.endswith("."):
                raise IllegalWindowsFilenameError(f'"{path_object}" path segment cannot end with a period on Windows')
            elif any(illegal_character in path_fragement for illegal_character in cls.ILLEGAL_CHARACTERS):
                raise IllegalWindowsFilenameError(f'"{path_object}" contains illegal characters on Windows')
            # Linux limits file names based on the byte length of the file name, not the number of characters
            # Byte length will always be less than the number of characters so just check the byte length
            if (len(path_fragement.encode("utf-8"))) > 255:
                raise IllegalLinuxFilenameError(f'"{path_fragement}" is too long to be a valid file name on Linux')

    # TypeErrors occur in __new__ so it needs to be where the type modifications take place
    def __new__(
        cls,
        *args: str | bytes | os.PathLike[str] | int | datetime | date | float,
        **kwargs: str,
    ) -> Self:
        path_objects: list[str | ExtendedPath | Path] = []
        args_list = list(args)

        # Convert all path segments to objects that Path can handle
        for path_fragment in args_list:
            path_objects.append(cls.__convert_to_string(path_fragment))

        return super().__new__(cls, *path_objects)

    def __truediv__(self, key: str | bytes | os.PathLike[str] | int | datetime | date | float) -> Self:
        return super().__truediv__(self.__convert_to_string(key))

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
        return datetime.fromtimestamp(self.stat().st_mtime).astimezone() > timestamp

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
