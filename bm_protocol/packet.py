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
from .packet_type import PacketType
from .device_type import DeviceType

class Packet:
    def __init__(self):
        self.sequence = 0
        self.channel = 0
        self.message = None
        self.device_name = ""
        self.buffer = amf3.ByteArray()
        self.device_id = ""
        self.timestamp = 0.0
        self.packet_type = PacketType.DATA
        self.device_type = DeviceType.SERVER
        self.rtt = 0.0

    def read_external(self, data_input):
        self.channel = data_input.readInt()
        self.sequence = data_input.readInt()
        self.timestamp = data_input.readDouble()
        self.rtt = data_input.readDouble()
        pt = data_input.readInt()
        self.packet_type = PacketType.for_value(pt)
        dt = data_input.readInt()
        self.device_type = DeviceType.for_value(dt)
        self.device_id = data_input.readUTF()
        self.device_name = data_input.readUTF()
        has_message = data_input.readBoolean()
        if has_message:
            self.message = data_input.readObject()

    def write_external(self, data_output):
        if hasattr(data_output, 'write_int'):
            data_output.write_int(self.channel)
            data_output.write_int(self.sequence)
            data_output.write_double(self.timestamp)
            data_output.write_double(self.rtt)
            data_output.write_int(self.packet_type.get_packet_type() if self.packet_type else 0)
            data_output.write_int(self.device_type.get_device_type() if self.device_type else 0)
            data_output.write_utf(self.device_id or "")
            data_output.write_utf(self.device_name or "")

            if self.message is not None:
                data_output.write_boolean(True)
                data_output.write_object(self.message)
            else:
                data_output.write_boolean(False)
        else:
            data_output.writeInt(self.channel)
            data_output.writeInt(self.sequence)
            data_output.writeDouble(self.timestamp)
            data_output.writeDouble(self.rtt)
            data_output.writeInt(self.packet_type.get_packet_type() if self.packet_type else 0)
            data_output.writeInt(self.device_type.get_device_type() if self.device_type else 0)
            data_output.writeUTF(self.device_id or "")
            data_output.writeUTF(self.device_name or "")

            if self.message is not None:
                data_output.writeBoolean(True)
                data_output.writeObject(self.message)
            else:
                data_output.writeBoolean(False)

    def size(self):
        temp_buffer = amf3.ByteArray()
        self.write_external(amf3.DataOutput(temp_buffer))
        return len(temp_buffer)

    def __str__(self):
        return (f"Packet [device_type={self.device_type}, device_id={self.device_id}, "
                f"device_name={self.device_name}, packet_type={self.packet_type}, "
                f"channel={self.channel}, sequence={self.sequence}, timestamp={self.timestamp}, "
                f"rtt={self.rtt}, message={self.message}]")