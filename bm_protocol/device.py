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

from .device_type import DeviceType

class Device:
    def __init__(self, device_id="", device_name="", address=None):
        self._device_id = device_id
        self.device_name = device_name
        self._address = address
        self.device_type = DeviceType.SERVER

    @property
    def device_id(self):
        return self._device_id

    @device_id.setter
    def device_id(self, value: str):
        self._device_id = value

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    def read_external(self, data_input):
        device_type_int = data_input.readInt()
        self.device_type = DeviceType.for_value(device_type_int)
        self.device_id = data_input.readUTF()
        self.device_name = data_input.readUTF()

    def write_external(self, data_output):
        if hasattr(data_output, 'write_int'):
            data_output.write_int(self.device_type.get_device_type() if self.device_type else 0)
            data_output.write_utf(self.device_id or "")
            data_output.write_utf(self.device_name or "")
        else:
            data_output.writeInt(self.device_type.get_device_type() if self.device_type else 0)
            data_output.writeUTF(self.device_id or "")
            data_output.writeUTF(self.device_name or "")