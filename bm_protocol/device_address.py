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

class DeviceAddress:
    def __init__(self, host="", port=0):
        self.host = host
        self.port = port

    def read_external(self, data_input):
        self.host = data_input.readUTF()
        data_input.readInt()
        self.port = data_input.readInt()

    def write_external(self, data_output):
        if hasattr(data_output, 'write_utf'):
            data_output.write_utf(self.host)
            data_output.write_int(self.port)
            data_output.write_int(self.port)
        else:
            data_output.writeUTF(self.host)
            data_output.writeInt(self.port)
            data_output.writeInt(self.port)

    def __str__(self):
        return f"DeviceAddress [host={self.host}, port={self.port}]"