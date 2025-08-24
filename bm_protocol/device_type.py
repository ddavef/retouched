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

class DeviceType:
    _ANY_DEVICE_TYPE = 0
    _UNITY_DEVICE_TYPE = 1
    _IPHONE_DEVICE_TYPE = 2
    _FLASH_DEVICE_TYPE = 3
    _ANDROID_DEVICE_TYPE = 4
    _NATIVE_DEVICE_TYPE = 5
    _PALM_DEVICE_TYPE = 6
    _SERVER_DEVICE_TYPE = 7

    # Pre-declare values for the IDE
    ANY = None
    UNITY = None
    IPHONE = None
    FLASH = None
    ANDROID = None
    NATIVE = None
    PALM = None
    SERVER = None
    values = []
    value_names = []

    _enum_created = False

    def __init__(self, value):
        if DeviceType._enum_created:
            raise RuntimeError("The enum is already created.")
        self._value = value

    @staticmethod
    def for_value(value):
        return DeviceType.values[value]

    @staticmethod
    def value(value):
        return DeviceType.value_names[value]

    def get_device_type(self):
        return self._value

    def to_string(self):
        return f"[DeviceType {DeviceType.value_names[self._value]}]"

    def __str__(self):
        return self.to_string()

DeviceType.ANY = DeviceType(DeviceType._ANY_DEVICE_TYPE)
DeviceType.UNITY = DeviceType(DeviceType._UNITY_DEVICE_TYPE)
DeviceType.IPHONE = DeviceType(DeviceType._IPHONE_DEVICE_TYPE)
DeviceType.FLASH = DeviceType(DeviceType._FLASH_DEVICE_TYPE)
DeviceType.ANDROID = DeviceType(DeviceType._ANDROID_DEVICE_TYPE)
DeviceType.NATIVE = DeviceType(DeviceType._NATIVE_DEVICE_TYPE)
DeviceType.PALM = DeviceType(DeviceType._PALM_DEVICE_TYPE)
DeviceType.SERVER = DeviceType(DeviceType._SERVER_DEVICE_TYPE)

DeviceType.values = [
    DeviceType.ANY,
    DeviceType.UNITY,
    DeviceType.IPHONE,
    DeviceType.FLASH,
    DeviceType.ANDROID,
    DeviceType.NATIVE,
    DeviceType.PALM,
    DeviceType.SERVER
]

DeviceType.value_names = [
    "ANY",
    "UNITY",
    "IPHONE",
    "FLASH",
    "ANDROID",
    "NATIVE",
    "PALM",
    "SERVER"
]
DeviceType._enum_created = True
