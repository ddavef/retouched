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

from pyamf import amf3

class ByteChunk:
    def __init__(self):
        self.size = 0
        self.raw_chunk = None
        self.chunk = None

    @property
    def size(self):
        return self.size

    @size.setter
    def size(self, value):
        self.size = value

    @property
    def raw_chunk(self):
        return self.raw_chunk

    @raw_chunk.setter
    def raw_chunk(self, value):
        self.raw_chunk = value

    @property
    def chunk(self):
        return self.chunk

    @chunk.setter
    def chunk(self, value):
        self.chunk = value

    @staticmethod
    def can_read(input_stream):
        if input_stream.remaining() > 4:
            size = (input_stream.readByte() & 0xFF |
                    (input_stream.readByte() & 0xFF) << 8 |
                    (input_stream.readByte() & 0xFF) << 16 |
                    (input_stream.readByte() & 0xFF) << 24)

            if input_stream.remaining() >= size:
                return True
        return False

    def read_external(self, input_stream):
        self.size = (input_stream.readByte() & 0xFF |
                     (input_stream.readByte() & 0xFF) << 8 |
                     (input_stream.readByte() & 0xFF) << 16 |
                     (input_stream.readByte() & 0xFF) << 24)

        expected_size = self.size
        self.raw_chunk = amf3.ByteArray()

        while expected_size > 0 and input_stream.remaining() > 0:
            self.raw_chunk.writeByte(input_stream.readByte())
            expected_size -= 1

    def write_external(self, output_stream):
        output_stream.writeByte(self.size & 0xFF)
        output_stream.writeByte((self.size >> 8) & 0xFF)
        output_stream.writeByte((self.size >> 16) & 0xFF)
        output_stream.writeByte((self.size >> 24) & 0xFF)

        if self.chunk is not None:
            if isinstance(self.chunk, bool):
                output_stream.writeObject(self.chunk)