"""
retouched
Copyright (C) 2025 ddavef/KinteLiX

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

class Version8Bit:
    def __init__(self):
        self._build = 0
        self._minor = 0
        self._major = 0

    def read_external(self, data_input):
        self._build = data_input.readByte()
        self._build |= data_input.readByte() << 8

        self._minor = data_input.readByte()
        self._major = data_input.readByte()

    def write_external(self, data_output):
        v_int = (self._major & 0xFF) << 24 | (self._minor & 0xFF) << 16 | self._build & 0xFFFF

        data_output.writeByte(v_int & 0xFF)
        data_output.writeByte((v_int >> 8) & 0xFF)
        data_output.writeByte((v_int >> 16) & 0xFF)
        data_output.writeByte((v_int >> 24) & 0xFF)

    @property
    def bits(self):
        return 32

    @property
    def build(self):
        return self._build

    @build.setter
    def build(self, value):
        self._build = value

    @property
    def minor(self):
        return self._minor

    @minor.setter
    def minor(self, value):
        self._minor = value

    @property
    def major(self):
        return self._major

    @major.setter
    def major(self, value):
        self._major = value

    def __str__(self):
        return f"Version8Bit({self._major}.{self._minor}.{self._build})"

    def __repr__(self):
        return f"Version8Bit(major={self._major}, minor={self._minor}, build={self._build})"