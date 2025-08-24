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

class BMArray(list):
    def __init__(self, *parameters):
        super().__init__()
        if parameters:
            self.extend(parameters)

    def read_external(self, data_input):
        self.clear()
        length = data_input.readShort()

        if length == 0:
            return

        for _ in range(length):
            encoding = data_input.readUTF()

            if encoding == "i":
                self.append(data_input.readInt())
            elif encoding == "I":
                self.append(data_input.readUnsignedInt())
            elif encoding == "s":
                self.append(data_input.readShort())
            elif encoding == "S":
                self.append(data_input.readUnsignedShort())
            elif encoding == "f":
                self.append(data_input.readFloat())
            elif encoding == "d":
                self.append(data_input.readDouble())
            elif encoding == "B":
                self.append(data_input.readBoolean())
            elif encoding == "*":
                self.append(data_input.readUTF())
            elif encoding == "@":
                self.append(data_input.readObject())
            else:
                print(f"Unable to read element with encoding: {encoding}")

    def write_external(self, data_output):
        data_output.writeShort(len(self))

        for value in self:
            if isinstance(value, int):
                if value >= 0 and value <= 4294967295:  # uint range
                    encoding = "I"
                else:
                    encoding = "i"
            elif isinstance(value, float):
                encoding = "f"
            elif isinstance(value, bool):
                encoding = "B"
            elif isinstance(value, str):
                encoding = "*"
            elif hasattr(value, 'read_external') and hasattr(value, 'write_external'):
                encoding = "@"
            else:
                print(f"Unrecognized object: {type(value)} {str(value)}")
                continue

            data_output.writeUTF(encoding)
            data_output.writeObject(value)

    def __str__(self):
        return f"BMArray [length={len(self)}]"