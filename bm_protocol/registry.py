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

from typing import Dict, Type, Optional, List, Any

from bm_protocol.bm_byte_chunk import BMByteChunk


class Registry:
    _global_id_to_class: Dict[int, Type] = {}
    _global_class_to_id: Dict[Type, int] = {}
    _global_initiated: bool = False

    def __init__(self, error_handler=None):
        self.error_handler = error_handler

        self._devices: Dict[str, Any] = {}
        self._flash_devices: Dict[str, Any] = {}

        self._initiated: bool = False
        self.init()

    def init(self):
        if self._initiated:
            return
        Registry.init_global()
        self._initiated = True
        if self.error_handler:
            self.error_handler.log_info("Registry initialized", "REGISTRY")

    @property
    def initiated(self) -> bool:
        return self._initiated

    @staticmethod
    def class_for_id(class_id: int) -> Optional[Type]:
        return Registry.class_for_id_global(class_id)

    @staticmethod
    def id_for_class(clazz: Type) -> Optional[int]:
        return Registry.id_for_class_global(clazz)

    def register_device(self, device: Any) -> bool:
        try:
            device_id = self._get_device_id(device)
            if device_id:
                if hasattr(device, 'device') and hasattr(device.device, 'device_type'):
                    from .device_type import DeviceType
                    if device.device.device_type in [DeviceType.FLASH, DeviceType.UNITY]:
                        return self.register_flash_device(device)

                self._devices[device_id] = device

                if self.error_handler:
                    self.error_handler.log_info(f"Device registered: {device_id}", "REGISTRY")
                return True
            return False
        except Exception as e:
            if self.error_handler:
                self.error_handler.log_error(f"Failed to register device: {e}", "REGISTRY")
            return False

    def register_flash_device(self, flash_device: Any) -> bool:
        try:
            device_id = self._get_device_id(flash_device)
            if device_id:
                self._flash_devices[device_id] = flash_device

                if self.error_handler:
                    self.error_handler.log_info(f"Flash device registered: {device_id}", "REGISTRY")
                return True
            return False
        except Exception as e:
            if self.error_handler:
                self.error_handler.log_error(f"Failed to register flash device: {e}", "REGISTRY")
            return False

    def unregister_device(self, device_id: str) -> bool:
        try:
            removed_device = device_id in self._devices
            removed_flash = device_id in self._flash_devices

            self._devices.pop(device_id, None)
            self._flash_devices.pop(device_id, None)

            if (removed_device or removed_flash) and self.error_handler:
                self.error_handler.log_info(f"Device unregistered: {device_id}", "REGISTRY")

            return removed_device or removed_flash
        except Exception as e:
            if self.error_handler:
                self.error_handler.log_error(f"Failed to unregister device {device_id}: {e}", "REGISTRY")
            return False

    def get_all_devices(self) -> List[Any]:
        return list(self._devices.values()) + list(self._flash_devices.values())

    def get_device_count(self) -> int:
        return len(self._devices) + len(self._flash_devices)

    @staticmethod
    def _get_device_id(device: Any) -> Optional[str]:
        for attr in ['device_id', 'id', 'deviceId', 'identifier', 'uuid']:
            if hasattr(device, attr):
                device_id = getattr(device, attr)
                if device_id is not None:
                    return str(device_id)
        return str(hash(device))

    @classmethod
    def init_global(cls):
        if cls._global_initiated:
            return

        try:
            from .packet import Packet
            from .device_address import DeviceAddress
            from .bm_array import BMArray
            from .bm_parameter import BMParameter
            from .bm_invoke import BMInvoke
            from .bm_registry_info import BMRegistryInfo
            from .flash_device import FlashDevice
            from .ping import Ping

            cls._global_id_to_class.clear()
            cls._global_class_to_id.clear()

            cls._register_class_global(Packet, 0)
            cls._register_class_global(DeviceAddress, 1)
            cls._register_class_global(BMParameter, 3)
            cls._register_class_global(BMInvoke, 4)

            for flash_id in (7, 8, 10, 15, 16, 17, 18):
                cls._register_class_global(FlashDevice, flash_id)

            cls._register_class_global(Ping, 11)
            cls._register_class_global(BMByteChunk, 14)
            cls._register_class_global(BMRegistryInfo, 19)
            cls._register_class_global(BMArray, 21)

            cls._global_initiated = True

        except Exception as e:
            print(f"Error initializing global registry: {e}")
            raise

    @classmethod
    def _register_class_global(cls, clazz: Type, class_id: int):
        existing = cls._global_id_to_class.get(class_id)
        if existing and existing is not clazz:
            raise ValueError(f"class id {class_id} is already mapped to {existing.__name__}, cannot map to {clazz.__name__}")
        cls._global_id_to_class[class_id] = clazz

        existing_id = cls._global_class_to_id.get(clazz)
        if existing_id is not None and existing_id != class_id:
            return
        if existing_id is None:
            cls._global_class_to_id[clazz] = class_id

    @classmethod
    def class_for_id_global(cls, class_id: int) -> Optional[Type]:
        if not cls._global_initiated:
            cls.init_global()
        return cls._global_id_to_class.get(class_id)

    @classmethod
    def id_for_class_global(cls, clazz: Type) -> Optional[int]:
        if not cls._global_initiated:
            cls.init_global()
        return cls._global_class_to_id.get(clazz)