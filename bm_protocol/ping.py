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
from typing import Any, Optional

class Ping:
    def __init__(self, uid: Optional[str] = None, addr: Optional[Any] = None):
        self.device_id = uid
        self.address = addr

    def writeExternal(self, data_output: amf3.DataOutput):
        data_output.writeUTF(self.device_id)
        data_output.writeObject(self.address)

    def readExternal(self, data_input: amf3.DataInput):
        self.device_id = data_input.readUTF()
        self.address = data_input.readObject()
