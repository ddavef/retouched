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
from typing import Any

class Stream:
    ERROR_DATA = ""

    def __init__(self, byte_array=None, registry=None):
        super().__init__()

        self.registry = registry
        self.data = None
        self.tt = 0
        self.tmp_array = amf3.ByteArray()

        self.byte_array: amf3.ByteArray = byte_array if byte_array else amf3.ByteArray()

        self.byte_array.seek(0)
        self.byte_array.endian = '<'  # Little-endian

        self._ensure_registry_initialized()

    def _ensure_registry_initialized(self):
        if self.registry and self.registry.initiated:
            return
        else:
            from registry import Registry
            Registry.init_global()

    def _get_class_for_id(self, class_id: int):
        if self.registry and self.registry.initiated:
            return self.registry.class_for_id(class_id)
        else:
            from registry import Registry
            return Registry.class_for_id_global(class_id)

    def read_short(self):
        return self.byte_array.readShort()

    def read_unsigned_short(self):
        return self.byte_array.readUnsignedShort()

    def read_utf(self):
        _len = self.byte_array.readShort()
        return self.byte_array.readUTFBytes(_len)

    def read_double(self):
        return self.byte_array.readDouble()

    def read_int(self):
        return self.byte_array.readInt()

    def read_byte(self):
        return self.byte_array.readByte()

    def read_boolean(self):
        return self.byte_array.readBoolean()

    def read_unsigned_int(self):
        return self.byte_array.readUnsignedInt()

    def read_float(self):
        return self.byte_array.readFloat()

    def write_byte(self, value: int):
        self.byte_array.writeByte(value)

    def write_utf_bytes(self, value: str):
        self.byte_array.writeUTFBytes(value)

    def write_int(self, value: int):
        self.byte_array.writeInt(value)

    def write_short(self, value: int):
        self.byte_array.writeShort(value)

    def write_float(self, value: float):
        self.byte_array.writeFloat(value)

    def write_multibyte(self, value: str, charset: str):
        self.byte_array.writeMultiByte(value, charset)

    def write_utf(self, value: str):
        if not value:
            value = ""
        temp = amf3.ByteArray()
        temp.endian = '<'  # Little-endian
        temp.writeUTFBytes(value)
        self.write_short(len(temp))
        temp.seek(0)
        while temp.remaining() > 0:
            self.byte_array.writeByte(temp.readByte())

    def write_boolean(self, value: bool):
        self.byte_array.writeBoolean(value)

    def write_double(self, value: float):
        self.byte_array.writeDouble(value)

    def write_unsigned_int(self, value: int):
        self.byte_array.writeUnsignedInt(value)

    def read_object(self):
        encoding: str = self.read_utf()
        if len(encoding) > 1:
            Stream.ERROR_DATA = encoding
            raise Exception("Bad parsing!")

        _type: int = self.read_short()

        obj_class = self._get_class_for_id(_type)

        if obj_class:
            instance = obj_class()
            if hasattr(instance, 'read_external'):
                instance.read_external(self)
            return instance

        print(f"DEBUG: No class registered for ID: {_type}")
        return None

    def write_object(self, obj: Any):
        if obj is None:
            self.write_utf("")
            self.write_short(0)
            return

        self.write_utf("@")

        obj_class = type(obj)
        registry_id = None

        if hasattr(self, 'registry') and self.registry:
            registry_id = self.registry.id_for_class(obj_class)

        if registry_id is None:
            from registry import Registry
            Registry.init_global()
            registry_id = Registry.id_for_class_global(obj_class)

        if registry_id is None:
            raise Exception(f"No registry ID found for class: {obj_class.__name__}")

        self.write_short(registry_id)

        if hasattr(obj, 'write_external'):
            obj.write_external(self)
        else:
            raise Exception(f"Object {obj_class.__name__} does not have write_external method")

    def readInt(self):
        return self.read_int()

    def readUTF(self):
        return self.read_utf()

    def readDouble(self):
        return self.read_double()

    def readBoolean(self):
        return self.read_boolean()

    def readShort(self):
        return self.read_short()

    def readUnsignedInt(self):
        return self.read_unsigned_int()

    def readFloat(self):
        return self.read_float()

    def readUnsignedShort(self):
        return self.read_unsigned_short()

    def readByte(self):
        return self.read_byte()

    def readObject(self):
        return self.read_object()

    def writeInt(self, value):
        self.write_int(value)

    def writeShort(self, value):
        self.write_short(value)

    def writeDouble(self, value):
        self.write_double(value)

    def writeFloat(self, value):
        self.write_float(value)

    def writeUnsignedInt(self, value):
        self.write_unsigned_int(value)

    def writeUTF(self, value):
        self.write_utf(value)

    def writeBoolean(self, value):
        self.write_boolean(value)

    def writeObject(self, obj):
        self.write_object(obj)

    def writeByte(self, value):
        self.write_byte(value)

    def writeUTFBytes(self, value):
        self.write_utf_bytes(value)

    def remaining(self):
        current_pos = self.byte_array.tell()
        self.byte_array.seek(0, 2)
        end_pos = self.byte_array.tell()
        self.byte_array.seek(current_pos)
        return end_pos - current_pos

    def getvalue(self):
        return self.byte_array.getvalue()

    def seek(self, position, whence=0):
        self.byte_array.seek(position, whence)

    def tell(self):
        return self.byte_array.tell()