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

class BMByteChunk:
    def __init__(self, set_id="", start_byte=0, chunk_size=0, total_bytes=0, byte_array=None):
        self.set_id = set_id
        self.start_byte = start_byte
        self.chunk_size = chunk_size
        self.total_size = total_bytes
        self.bytes = byte_array if byte_array is not None else amf3.ByteArray()

    def read_external(self, data_input):
        self.set_id = data_input.readUTF()
        self.start_byte = data_input.readInt()
        self.chunk_size = data_input.readInt()
        self.total_size = data_input.readInt()

        self.bytes = amf3.ByteArray()
        self.bytes.endian = 'little'

        j = 0
        while j < self.chunk_size:
            self.bytes.writeByte(data_input.readByte())
            j += 1

        self.bytes.seek(0)

    @property
    def chunk(self):
        return self.bytes

    def write_external(self, data_output):
        data_output.writeUTF(self.set_id)
        data_output.writeInt(self.start_byte)
        data_output.writeInt(self.chunk_size)
        data_output.writeInt(self.total_size)

        if self.bytes is not None:
            original_position = self.bytes.tell()
            self.bytes.seek(self.start_byte)

            for i in range(self.chunk_size):
                if self.bytes.remaining() > 0:
                    data_output.writeByte(self.bytes.readByte())
                else:
                    break

            self.bytes.seek(original_position)