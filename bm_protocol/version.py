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

class VersionPacket:
    _versions = []

    def __init__(self, stream, packet_size):
        self._size = packet_size
        self._min_version = None
        self._packet = stream
        self._version = None
        version_bits = (self._size // 2) * 8
        self._version = self.get_version_reader(version_bits)
        self._min_version = self.get_version_reader(version_bits)

    def get_size(self):
        return self._size

    def get_min_version(self):
        return self._min_version

    def set_version(self, value):
        self._version = value

    def set_min_version(self, value):
        self._min_version = value

    def to_string(self):
        return f"VersionPacket(version={self._version}, min_version={self._min_version})"

    def get_version_reader(self, bits):
        for version in self._versions:
            if hasattr(version, 'bits') and version.bits == bits:
                version_class = type(version)
                return version_class()
        return None

    def read_external(self, data_input):
        self._version = self.get_version_reader(self._size / 2 * 8)
        self._min_version = self.get_version_reader(self._size / 2 * 8)
        if self._version and hasattr(self._version, 'read_external'):
            self._version.read_external(data_input)

        if self._min_version and hasattr(self._min_version, 'read_external'):
            self._min_version.read_external(data_input)

    def write_external(self, data_output):
        data_output.writeByte(8 & 0xFF)
        data_output.writeByte((8 >> 8) & 0xFF)
        data_output.writeByte((8 >> 16) & 0xFF)
        data_output.writeByte((8 >> 24) & 0xFF)
        if self._version and hasattr(self._version, 'write_external'):
            self._version.write_external(data_output)

        if self._min_version and hasattr(self._min_version, 'write_external'):
            self._min_version.write_external(data_output)