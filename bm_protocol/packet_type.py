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

class PacketType:
    DATA_PACKETTYPE = 0
    PING_PACKETTYPE = 1
    ACK_PACKETTYPE = 2
    ECHO_PACKETTYPE = 3
    ANALYSIS_PACKETTYPE = 4
    KEEP_ALIVE_PACKETTYPE = 5

    # Pre-declare values for the IDE
    DATA = None
    PING = None
    ACK = None
    ECHO = None
    ANALYSIS = None
    KEEP_ALIVE = None
    values = []
    value_names = []

    _enum_created = False

    def __init__(self, value):
        if PacketType._enum_created:
            raise RuntimeError("The enum is already created.")
        self._value = value

    @staticmethod
    def for_value(value):
        return PacketType.values[value]

    def get_packet_type(self):
        return self._value

    def to_string(self):
        return f"[PacketType {PacketType.value_names[self._value]}]"

    def __str__(self):
        return self.to_string()

PacketType.DATA = PacketType(PacketType.DATA_PACKETTYPE)
PacketType.PING = PacketType(PacketType.PING_PACKETTYPE)
PacketType.ACK = PacketType(PacketType.ACK_PACKETTYPE)
PacketType.ECHO = PacketType(PacketType.ECHO_PACKETTYPE)
PacketType.ANALYSIS = PacketType(PacketType.ANALYSIS_PACKETTYPE)
PacketType.KEEP_ALIVE = PacketType(PacketType.KEEP_ALIVE_PACKETTYPE)

PacketType.values = [
    PacketType.DATA,
    PacketType.PING,
    PacketType.ACK,
    PacketType.ECHO,
    PacketType.ANALYSIS,
    PacketType.KEEP_ALIVE
]

PacketType.value_names = [
    "DATA",
    "PING",
    "ACK",
    "ECHO",
    "ANALYSIS",
    "KEEP_ALIVE"
]
PacketType._enum_created = True