from datetime import date, datetime
from pathlib import Path

import pytest

from extended_path import ExtendedPath, IllegalLinuxFilenameError, IllegalWindowsFilenameError


# Test by converting the ExtendedPath to a Path because testing against ExtendedPath directly may hide bugs
class TestConversions:
    def test_integer(self):
        assert Path(ExtendedPath(123)) == Path("123")

    def test_float(self):
        assert Path(ExtendedPath(123.456)) == ExtendedPath("123.456")

    def test_date(self):
        assert Path(ExtendedPath(date(2020, 1, 1))) == ExtendedPath("2020-01-01")

    def test_path(self):
        assert Path(ExtendedPath(Path("123"))) == ExtendedPath("123")

    def test_extended_path(self):
        assert Path(ExtendedPath(ExtendedPath("123"))) == ExtendedPath("123")

    def test_datetime(self):
        assert Path(ExtendedPath(datetime(2020, 1, 1).timestamp())) == ExtendedPath("1577865600.0")


class TestIllegalNames:
    BASE_PATH = ExtendedPath("Base")

    ILLEGAL_WINDOWS_FILE_NAMES = (
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
        "Ends With Space ",
        "Ends With Period.",
        "..",  # Not technically a file name, but just avoid using it
        ".",  # Not technically a file name, but just avoid using it
    )

    ILLEGAL_WINDOWS_CHARACTERS = (
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

    def test_windows_illegal_name_initialization(self):
        for string in self.ILLEGAL_WINDOWS_FILE_NAMES:
            with pytest.raises(IllegalWindowsFilenameError):
                ExtendedPath(string)

    def test_windows_illegal_name_append(self):
        for string in self.ILLEGAL_WINDOWS_FILE_NAMES:
            with pytest.raises(IllegalWindowsFilenameError):
                _ = self.BASE_PATH / string

    def test_illegal_name_initialization_with_extension(self):
        # TODO: Not sure why this test fails, even though the error is raised
        for string in self.ILLEGAL_WINDOWS_CHARACTERS:
            with pytest.raises(IllegalWindowsFilenameError):
                ExtendedPath(f"{string}.ext")

    def test_illegal_name_addition_with_extension(self):
        # TODO: Not sure why this test fails, even though the error is raised
        base_path = ExtendedPath("Base")
        for string in self.ILLEGAL_WINDOWS_CHARACTERS:
            with pytest.raises(IllegalWindowsFilenameError):
                _ = base_path / f"{string}.ext"

    def test_illegal_character_initialization(self):
        for character in self.ILLEGAL_WINDOWS_CHARACTERS:
            with pytest.raises(IllegalWindowsFilenameError):
                ExtendedPath(character)

    def test_illegal_character_append(self):
        for character in self.ILLEGAL_WINDOWS_CHARACTERS:
            with pytest.raises(IllegalWindowsFilenameError):
                _ = self.BASE_PATH / character

    def test_long_file_name(self):
        with pytest.raises(IllegalLinuxFilenameError):
            ExtendedPath("👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨")

    def test_long_file_name_append(self):
        with pytest.raises(IllegalLinuxFilenameError):
            _ = self.BASE_PATH / "👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨👩‍❤️‍💋‍👨"


class TestUpToDate:
    def test_up_to_date_no_file(self):
        timestamp = datetime.now()
        file = ExtendedPath("Temp Test Files/test_up_to_date_no_file.ext")
        file.parent.delete()
        assert not file.up_to_date(timestamp)

    def test_up_to_date_no_file_or_timestamp(self):
        file = ExtendedPath("Temp Test Files/test_up_to_date_no_file.ext")
        file.parent.delete()
        assert not file.up_to_date()

    def test_up_to_date_new_file(self):
        timestamp = datetime.now()
        file = ExtendedPath("Temp Test Files/test_up_to_date_new_file.ext")
        file.write("Text")
        assert file.up_to_date(timestamp)
        file.parent.delete()

    def test_up_to_date_old_file(self):
        file = ExtendedPath("Temp Test Files/test_up_to_date_old_file.ext")
        file.write("Text")
        timestamp = datetime.now()
        assert not file.up_to_date(timestamp)
        file.parent.delete()


class TestWrite:
    def test_write_binary(self):
        file = ExtendedPath("Temp Test Files/test_write_binary.ext")
        file.write(b"Text")
        assert file.read_bytes() == b"Text"
        file.parent.delete()

    def test_write_text(self):
        file = ExtendedPath("Temp Test Files/test_write_text.ext")
        file.write("Text")
        assert file.read_text() == "Text"
        file.parent.delete()


class TestDelete:
    def delete_file(self):
        file = ExtendedPath("Temp Test Files/test_delete_file.ext")
        file.write("Text")
        file.delete()
        assert file.exists()

    def delete_empty_folder(self):
        folder = ExtendedPath("Temp Test Files/test_delete_empty_folder")
        folder.mkdir()
        folder.delete()
        assert folder.exists()

    def delete_non_empty_folder(self):
        folder = ExtendedPath("Temp Test Files/test_delete_non_empty_folder")
        folder.mkdir()
        file = folder / "test_delete_non_empty_folder.ext"
        file.write("Text")
        folder.delete()
        assert folder.exists()
