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

from .device import Device
from .device_type import DeviceType

class FlashDevice(Device):
    def __init__(self, device_id="", device_name="", address=None, device_type=None):
        super().__init__(device_id, address)
        self.device_name = device_name
        self.device_type = device_type if device_type is not None else DeviceType.FLASH

    def read_external(self, data_input):
        super().read_external(data_input)

    def write_external(self, data_output):
        super().write_external(data_output)

    def __str__(self):
        return f"FlashDevice [device_id={self.device_id}, device_name={self.device_name}, address={self.address}]"