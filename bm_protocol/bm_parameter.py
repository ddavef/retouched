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

class BMParameter:
    def __init__(self, default_value=None):
        self.encoding = None
        self.value = None

        if default_value is not None:
            if isinstance(default_value, BMParameter):
                self.value = default_value.value
            else:
                self.value = default_value

            if isinstance(self.value, int):
                self.encoding = "i"
            elif isinstance(self.value, float):
                self.encoding = "f"
            elif isinstance(self.value, bool):
                self.encoding = "B"
            elif isinstance(self.value, str):
                self.encoding = "*"
            elif hasattr(self.value, 'read_external') and hasattr(self.value, 'write_external'):
                self.encoding = "@"
            else:
                raise ValueError(f"Unrecognized object: {type(self.value)} {self.value}")

    def read_external(self, data_input):
        self.encoding = data_input.readUTF()

        if self.encoding == "i":
            self.value = data_input.readInt()
        elif self.encoding == "I":
            self.value = data_input.readUnsignedInt()
        elif self.encoding == "s":
            self.value = data_input.readShort()
        elif self.encoding == "S":
            self.value = data_input.readUnsignedShort()
        elif self.encoding == "f":
            self.value = data_input.readFloat()
        elif self.encoding == "d":
            self.value = data_input.readDouble()
        elif self.encoding == "B":
            self.value = data_input.readBoolean()
        elif self.encoding == "*":
            self.value = data_input.readUTF()
        elif self.encoding == "@":
            self.value = data_input.readObject()

    def write_external(self, data_output):
        if hasattr(data_output, 'write_utf'):
            data_output.write_utf(self.encoding)
            self._write_value_stream(data_output)
        else:
            data_output.writeUTF(self.encoding)
            self._write_value_dataoutput(data_output)

    def _write_value_stream(self, data_output):
        if self.value is not None:
            if self.encoding == "i":
                data_output.write_int(self.value)
            elif self.encoding == "I":
                data_output.write_unsigned_int(self.value)
            elif self.encoding in ["s", "S"]:
                data_output.write_short(self.value)
            elif self.encoding == "f":
                data_output.write_float(self.value)
            elif self.encoding == "d":
                data_output.write_double(self.value)
            elif self.encoding == "B":
                data_output.write_boolean(self.value)
            elif self.encoding == "*":
                data_output.write_utf(self.value)
            elif self.encoding == "@":
                data_output.write_object(self.value)

    def _write_value_dataoutput(self, data_output):
        if self.value is not None:
            if self.encoding == "i":
                data_output.writeInt(self.value)
            elif self.encoding == "I":
                data_output.writeUnsignedInt(self.value)
            elif self.encoding in ["s", "S"]:
                data_output.writeShort(self.value)
            elif self.encoding == "f":
                data_output.writeFloat(self.value)
            elif self.encoding == "d":
                data_output.writeDouble(self.value)
            elif self.encoding == "B":
                data_output.writeBoolean(self.value)
            elif self.encoding == "*":
                data_output.writeUTF(self.value)
            elif self.encoding == "@":
                data_output.writeObject(self.value)

    def __str__(self):
        return f"BMParameter [encoding={self.encoding}, value={self.value.__str__()}]"