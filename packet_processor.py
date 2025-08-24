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

import time
from pyamf import amf3
from pyamf import register_class
from typing import Optional
from bm_protocol.packet_type import PacketType
from bm_protocol.bm_invoke import BMInvoke
from bm_protocol.bm_parameter import BMParameter
from bm_protocol.bm_array import BMArray
from bm_protocol.bm_byte_chunk import BMByteChunk
from bm_protocol.byte_chunk import ByteChunk
from bm_protocol.ping import Ping
from bm_protocol.device import Device
from bm_protocol.flash_device import FlashDevice
from bm_protocol.device_address import DeviceAddress
from bm_protocol.device_type import DeviceType
from bm_protocol.bm_registry_info import BMRegistryInfo
from bm_protocol.version import VersionPacket as Version
from bm_protocol.version_8bit import Version8Bit
from bm_protocol.stream import Stream
from bm_protocol.registry import Registry
from bm_protocol.packet import Packet

class PacketProcessor:
    def __init__(self, error_handler=None, registry=None):
        self.error_handler = error_handler
        self.registry = registry
        self._register_amf_classes()

    @staticmethod
    def _register_amf_classes():
        """
        Registers AMF classes for use with pyamf.
        """
        register_class(Packet, 'Packet')
        register_class(BMInvoke, 'BMInvoke')
        register_class(BMParameter, 'BMParameter')
        register_class(BMArray, 'BMArray')
        register_class(BMByteChunk, 'BMByteChunk')
        register_class(ByteChunk, 'ByteChunk')
        register_class(Ping, 'Ping')
        register_class(Device, 'Device')
        register_class(FlashDevice, 'FlashDevice')
        register_class(DeviceAddress, 'DeviceAddress')
        register_class(BMRegistryInfo, 'BMRegistryInfo')
        register_class(Version, 'Version')
        register_class(Version8Bit, 'Version8Bit')
        register_class(Stream, 'Stream')

    @staticmethod
    def create_invoke_packet(method: str, params: list = None, sequence: int = 1,
                             return_method: str = None, device_id: str = None,
                             device_name: str = None, packet_type=None, device_type=None,
                             timestamp: float = None) -> 'Packet':
        """
        Creates the invoke packet.
        BMInvoke works by having a method name and optionally a callback and a list of parameters.
        This method constructs a Packet containing a BMInvoke message.
        """
        invoke = BMInvoke()
        invoke.id = sequence
        invoke.method = method
        if return_method:
            invoke.return_method = return_method
        if params:
            for param in params:
                invoke.add_parameter(param)

        packet = Packet()
        packet.sequence = sequence
        packet.timestamp = timestamp if timestamp is not None else time.time() * 1000
        packet.packet_type = packet_type or PacketType.DATA
        packet.device_type = device_type or DeviceType.SERVER
        packet.device_id = device_id or "server"
        packet.device_name = device_name or "Server"
        packet.message = invoke

        return packet

    @staticmethod
    def create_version_packet() -> bytes:
        version_packet = Version(None, 8)

        current_version = Version8Bit()
        current_version.major = 2
        current_version.minor = 0
        current_version.build = 0
        version_packet.set_version(current_version)

        min_version = Version8Bit()
        min_version.major = 2
        min_version.minor = 0
        min_version.build = 0
        version_packet.set_min_version(min_version)

        output_buffer = amf3.ByteArray()
        data_output = amf3.DataOutput(output_buffer)
        version_packet.write_external(data_output)

        return output_buffer.getvalue()

    @staticmethod
    def create_registration_response_packet(original_invoke, server_device_id: str,
                                            server_host: str, server_port: int) -> 'Packet':

        server_address = DeviceAddress(host=server_host, port=server_port)
        server_device = FlashDevice(
            device_id=server_device_id,
            device_name="Registry",
            address=server_address
        )
        server_device.device_type = DeviceType.SERVER

        registry_info = BMRegistryInfo()
        registry_info.device = server_device
        registry_info.address = server_address
        registry_info.app_id = "Registry"
        registry_info.slot_id = 0

        return_method = getattr(original_invoke, 'return_method', None) or "onRegister"
        response = BMInvoke(iid=original_invoke.id, method=return_method)
        response.add_parameter(BMParameter(registry_info))

        packet = Packet()
        packet.sequence = original_invoke.id
        packet.timestamp = time.time() * 1000
        packet.packet_type = PacketType.DATA
        packet.device_type = DeviceType.SERVER
        packet.device_id = server_device_id
        packet.device_name = "Registry"
        packet.message = response

        return packet

    def create_response_packet(self, packet_obj) -> Optional[bytes]:
        try:
            if not isinstance(packet_obj, Packet):
                self.error_handler.log_warning(
                    f"Expected Packet object, got: {type(packet_obj).__name__}",
                    "PACKET_PROCESSOR"
                )
                return None

            Registry.init_global()

            output_buffer = amf3.ByteArray()
            output_buffer.endian = '<'

            output_buffer.writeShort(1)
            output_buffer.writeByte(ord("@"))

            packet_registry_id = Registry.id_for_class_global(Packet)
            if packet_registry_id is None:
                self.error_handler.log_error("No registry ID for Packet class", "PACKET_PROCESSOR")
                return None

            output_buffer.writeShort(packet_registry_id)

            class DataOutputWrapper:
                def __init__(self, buffer):
                    self.buffer = buffer

                def writeInt(self, value):
                    self.buffer.writeInt(value)

                def writeShort(self, value):
                    self.buffer.writeShort(value)

                def writeDouble(self, value):
                    self.buffer.writeDouble(value)

                def writeFloat(self, value):
                    self.buffer.writeFloat(value)

                def writeUnsignedInt(self, value):
                    self.buffer.writeUnsignedInt(value)

                def writeUTF(self, value):
                    if not value:
                        value = ""
                    temp = amf3.ByteArray()
                    temp.endian = '<'
                    temp.writeUTFBytes(value)
                    self.buffer.writeShort(len(temp))
                    temp.seek(0)
                    while temp.remaining() > 0:
                        self.buffer.writeByte(temp.readByte())

                def writeBoolean(self, value):
                    self.buffer.writeBoolean(value)

                def writeObject(self, obj):
                    if hasattr(obj, 'write_external'):
                        self.buffer.writeShort(1)
                        self.buffer.writeByte(ord("@"))

                        obj_registry_id = Registry.id_for_class_global(type(obj))
                        if obj_registry_id is not None:
                            self.buffer.writeShort(obj_registry_id)
                            obj.write_external(self)
                        else:
                            raise Exception(f"No registry ID for class: {type(obj)}")

            wrapper = DataOutputWrapper(output_buffer)
            packet_obj.write_external(wrapper)

            packet_content = output_buffer.getvalue()

            if len(packet_content) == 0:
                self.error_handler.log_warning("Empty packet data generated", "PACKET_PROCESSOR")
                return None

            size = len(packet_content)
            header_ba = amf3.ByteArray()
            header_ba.endian = '<'
            header_ba.writeUnsignedInt(size)

            final_packet = header_ba.getvalue() + packet_content

            self.error_handler.log_debug(
                f"Created packet with {len(final_packet)} bytes (header: {len(header_ba.getvalue())}, content: {len(packet_content)})",
                "PACKET_PROCESSOR"
            )

            return final_packet

        except Exception as e:
            self.error_handler.handle_client_error(
                None, e, "creating response packet"
            )
            return None