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
from bm_protocol.device_address import DeviceAddress
from bm_protocol.flash_device import FlashDevice
from bm_protocol.device_type import DeviceType
from bm_protocol.packet import Packet
from bm_protocol.packet_type import PacketType

class PacketOperationsMixin:
    def __init__(self):
        self.packet_processor = None
        self.error_handler = None
        self.socket = None
        self.device_id = None
        self.device_name = None

    def send_invoke_packet_to_socket(self, socket_obj, method: str, params: list = None,
                                     sequence: int = 1, return_method: str = None,
                                     device_id: str = None, device_name: str = None,
                                     packet_type=None, device_type=None, timestamp: float = None) -> bool:
        try:
            packet = self.packet_processor.create_invoke_packet(
                method=method, params=params, sequence=sequence,
                return_method=return_method,
                device_id=device_id or self.device_id,
                device_name=device_name or self.device_name,
                packet_type=packet_type, device_type=device_type,
                timestamp=timestamp
            )
            if packet is None:
                self.error_handler.log_error(f"create_invoke_packet returned None for method '{method}'",
                                             "PACKET_OPERATIONS")
                return False

            packet_data = self.packet_processor.create_response_packet(packet)
            if not packet_data:
                self.error_handler.log_error(f"create_response_packet returned no data for method '{method}'",
                                             "PACKET_OPERATIONS")
                return False

            socket_obj.sendall(packet_data)
            self.error_handler.log_info(f"Sent {method} packet", "PACKET_OPERATIONS")
            return True
        except Exception as e:
            self.error_handler.log_error(f"Failed to send invoke packet {method}: {e}", "PACKET_OPERATIONS")
            return False

    def send_raw_packet_to_socket(self, socket_obj, message,
                                  packet_type=PacketType.DATA,
                                  device_type=DeviceType.ANDROID,
                                  sequence: int = 1,
                                  timestamp: float | None = None) -> bool:
        try:
            packet = Packet()
            packet.sequence = sequence or 1
            packet.timestamp = timestamp if timestamp is not None else time.time() * 1000
            packet.packet_type = packet_type or PacketType.DATA
            packet.device_type = device_type or DeviceType.ANDROID
            packet.device_id = self.device_id
            packet.device_name = self.device_name
            packet.message = message

            packet_data = self.packet_processor.create_response_packet(packet)
            if not packet_data:
                self.error_handler.log_error("send_raw_packet_to_socket: no data from create_response_packet",
                                             "PACKET_OPERATIONS")
                return False

            socket_obj.sendall(packet_data)
            self.error_handler.log_info("Sent raw packet", "PACKET_OPERATIONS")
            return True
        except Exception as e:
            self.error_handler.log_error(f"Failed to send raw packet: {e}", "PACKET_OPERATIONS")
            return False

    def send_version_packet_to_socket(self, socket_obj) -> bool:
        try:
            handshake_data = self.packet_processor.create_version_packet()
            socket_obj.send(handshake_data)
            self.error_handler.log_debug("Version packet sent", "PACKET_OPERATIONS")
            return True
        except Exception as e:
            self.error_handler.log_error(f"Failed to send version packet: {e}", "PACKET_OPERATIONS")
            return False

    def send_registration_response_to_socket(self, socket_obj, original_invoke, server_device_id: str,
                                           server_host: str, server_port: int) -> bool:
        try:
            packet = self.packet_processor.create_registration_response_packet(
                original_invoke, server_device_id, server_host, server_port
            )
            packet_data = self.packet_processor.create_response_packet(packet)
            if packet_data:
                socket_obj.sendall(packet_data)
                self.error_handler.log_info("Sent registration response", "PACKET_OPERATIONS")
                return True
            return False
        except Exception as e:
            self.error_handler.log_error(f"Failed to send registration response: {e}", "PACKET_OPERATIONS")
            return False

    @staticmethod
    def create_relay_packet_common(sender_device_id: str, sender_device_name: str,
                                   sender_device_type, relay_message, server_device_id: str = None):
        relay_packet = Packet()
        relay_packet.sequence = getattr(relay_message, 'id', 1)
        relay_packet.timestamp = time.time() * 1000
        relay_packet.packet_type = PacketType.DATA
        relay_packet.device_type = sender_device_type or DeviceType.SERVER
        relay_packet.device_id = sender_device_id or server_device_id or "unknown"
        relay_packet.device_name = sender_device_name or "Unknown"
        relay_packet.message = relay_message
        return relay_packet

    def send_ping_response_to_socket(self, socket_obj, server_device_id: str, server_host: str, server_port: int) -> bool:
        try:
            server_address = DeviceAddress(host=server_host, port=server_port)
            server_device = FlashDevice(
                device_id=server_device_id,
                device_name="Registry",
                address=server_address
            )
            server_device.device_type = DeviceType.SERVER

            packet = Packet()
            packet.sequence = 1
            packet.timestamp = time.time() * 1000
            packet.packet_type = PacketType.PING
            packet.device_type = DeviceType.SERVER
            packet.device_id = server_device_id
            packet.device_name = "Registry"
            packet.message = server_device

            packet_data = self.packet_processor.create_response_packet(packet)
            if packet_data:
                socket_obj.sendall(packet_data)
                self.error_handler.log_info("Sent ping response", "PACKET_OPERATIONS")
                return True
            return False
        except Exception as e:
            self.error_handler.log_error(f"Failed to send ping response: {e}", "PACKET_OPERATIONS")
            return False