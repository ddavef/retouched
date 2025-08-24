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

import socket
import threading
from typing import Dict, Any, Callable
from pyamf import amf3
from packet_processor import PacketProcessor
from error_handler import ErrorHandler
from bm_protocol.registry import Registry
from packet_operations_mixin import PacketOperationsMixin
from bm_protocol.packet import Packet
from bm_protocol.bm_invoke import BMInvoke
from bm_protocol.bm_parameter import BMParameter
from bm_protocol.packet_type import PacketType
from bm_protocol.stream import Stream

class ClientHandler(PacketOperationsMixin):
    def __init__(self, client_socket: socket.socket, client_address: tuple,
                 packet_processor: PacketProcessor, error_handler: ErrorHandler,
                 registry: 'Registry' = None,
                 message_handlers: Dict[str, Callable] = None,
                 on_disconnect_callback: Callable = None):
        PacketOperationsMixin.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.packet_processor = packet_processor
        self.error_handler = error_handler
        self.registry = registry
        self.message_handlers = message_handlers or {}

        self.is_running = False
        self.client_thread = None
        self.device_id = ""
        self.device_name = ""
        self.last_ping_time = 0
        self.slot_id = None
        self.client_info = None

        self.receive_buffer = b''
        self.buffer_lock = threading.Lock()

        self.on_disconnect_callback = on_disconnect_callback
        self._disconnect_notified = False

        from pyamf import amf3
        self.buffer = amf3.ByteArray()
        self.buffer.endian = '<'
        self.version_handshake_complete = False

    def start(self):
        self.is_running = True

        if not self._handle_handshake():
            self.error_handler.log_error(
                f"Handshake failed for {self.client_address[0]}:{self.client_address[1]}",
                "CLIENT_HANDLER"
            )
            self.stop()
            return False

        self.client_thread = threading.Thread(target=self._handle_client, daemon=True)
        self.client_thread.start()

        self.error_handler.log_info(
            f"Client handler started for {self.client_address[0]}:{self.client_address[1]}",
            "CLIENT_HANDLER"
        )
        return True

    def stop(self):
        self.is_running = False
        try:
            self._notify_disconnection()
        except Exception:
            pass
        try:
            if self.client_socket:
                self.client_socket.close()
        except:
            pass
        if self.client_thread and self.client_thread.is_alive():
            self.client_thread.join(timeout=1.0)
        self.error_handler.log_info(
            f"Client handler stopped for {self.client_address[0]}:{self.client_address[1]}",
            "CLIENT_HANDLER"
        )

    def send_invoke_packet(self, method: str, params: list = None, sequence: int = 1,
                           return_method: str = None, device_id: str = None,
                           device_name: str = None, packet_type=None, device_type=None,
                           timestamp: float = None) -> bool:
        return self.send_invoke_packet_to_socket(
            self.client_socket, method, params, sequence, return_method,
            device_id, device_name, packet_type, device_type, timestamp
        )

    def send_registration_response(self, original_invoke, server_device_id: str,
                                   server_host: str, server_port: int) -> bool:
        return self.send_registration_response_to_socket(
            self.client_socket, original_invoke, server_device_id, server_host, server_port
        )

    def notify_host_connected(self) -> bool:
        try:
            info = getattr(self, "client_info", None)
            if not info:
                self.error_handler.log_warning("notify_host_connected: missing client_info", "CLIENT_HANDLER")
                return False

            invoke = BMInvoke(iid=1, method="onHostConnected")
            invoke.add_parameter(BMParameter(info))

            pkt = Packet()
            pkt.message = invoke

            ok = self.send_packet(pkt)
            if ok:
                self.error_handler.log_info(
                    f"Sent onHostConnected to {self.client_address[0]}:{self.client_address[1]} "
                    f"with slot {getattr(info, 'slot_id', 0)}",
                    "CLIENT_HANDLER"
                )
            else:
                self.error_handler.log_warning("Failed sending onHostConnected", "CLIENT_HANDLER")
            return ok
        except Exception as e:
            self.error_handler.handle_client_error(self.client_address, e, "notify host connected")
            return False

    def _handle_handshake(self) -> bool:
        """
        Performs the handshake with clients.
        The handshake is performed by exchanging the version packet.
        """
        try:
            self.client_socket.setblocking(False)
            try:
                client_version_pkt = self.client_socket.recv(12)
                if not client_version_pkt:
                    self.error_handler.log_warning(
                        f"Client disconnected before handshake: {self.client_address[0]}:{self.client_address[1]}",
                        "HANDSHAKE"
                    )
                    return False
                elif len(client_version_pkt) < 12:
                    self.error_handler.log_warning(
                        f"Failed to read full handshake (got {len(client_version_pkt)} bytes) from {self.client_address[0]}:{self.client_address[1]}",
                        "HANDSHAKE"
                    )
                    return False
                else:
                    self.error_handler.log_info(
                        f"Handshake received from {self.client_address[0]}:{self.client_address[1]}: {client_version_pkt.hex()}",
                        "HANDSHAKE"
                    )

            except BlockingIOError:
                self.error_handler.log_info(
                    f"No initial payload from client {self.client_address[0]}:{self.client_address[1]}, proceeding with handshake",
                    "HANDSHAKE"
                )
            except socket.error as e:
                self.error_handler.log_error(
                    f"Socket error during handshake read from {self.client_address[0]}:{self.client_address[1]}: {e}",
                    "HANDSHAKE"
                )
                return False
            finally:
                self.client_socket.setblocking(True)
                self.client_socket.settimeout(30.0)

            success = self.send_version_handshake()
            if success:
                self.version_handshake_complete = True

            return success

        except Exception as e:
            self.error_handler.handle_client_error(
                self.client_address, e, "handling handshake"
            )
            return False

    def _notify_disconnection(self):
        if self._disconnect_notified:
            return
        self._disconnect_notified = True
        self.is_running = False
        self.error_handler.log_info(
            f"Client marked disconnected: {self.client_address[0]}:{self.client_address[1]}",
            "CLIENT_HANDLER"
        )

    def send_version_handshake(self) -> bool:
        return self.send_version_packet_to_socket(self.client_socket)

    def _handle_client(self):
        while self.is_running:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    self.error_handler.log_info(
                        f"Client {self.client_address[0]}:{self.client_address[1]} disconnected",
                        "CLIENT_HANDLER"
                    )
                    self._notify_disconnection()
                    break

                self._process_received_data(data)

            except socket.timeout:
                continue
            except socket.error as e:
                if self.is_running:
                    self.error_handler.handle_client_error(
                        self.client_address, e, "receiving data"
                    )
                self._notify_disconnection()
                break
            except Exception as e:
                self.error_handler.handle_client_error(
                    self.client_address, e, "handling client"
                )
                self._notify_disconnection()
                break

    def _process_received_data(self, data: bytes):
        try:
            # Version packets don't need additional processing
            if len(data) == 12 or len(data) == 8:
                return

            with self.buffer_lock:
                if not hasattr(self, 'buffer'):
                    self.buffer = amf3.ByteArray()
                    self.buffer.endian = '<'

                self.buffer.seek(0, 2)
                self.buffer.write(data)
                self.buffer.seek(0)

                while self._parse_packet_from_buffer():
                    pass

        except Exception as e:
            self.error_handler.handle_client_error(
                self.client_address, e, "processing received data"
            )

            self.error_handler.log_debug(
                f"Raw packet data: {data.hex()}",
                "PACKET_DEBUG"
            )

    def _parse_packet_from_buffer(self) -> bool:
        """
        Parse one length‑prefixed packet from the receive buffer, if fully available.
        The first 4 bytes are an unsigned int payload length.
        Returns True if a packet was consumed (even on parse error) to make forward progress.
        """
        try:
            self.buffer.seek(0)

            # We need at least 4 bytes for the length prefix.
            if self.buffer.remaining() < 4:
                return False

            packet_size = self.buffer.readUnsignedInt()
            self.error_handler.log_debug(f"Packet size: {packet_size}", "PACKET_PARSER")

            # Wait for the full packet to arrive.
            if self.buffer.remaining() < packet_size:
                return False

            # Slice exactly one packet and compact the buffer afterward.
            packet_data = amf3.ByteArray()
            packet_data.endian = '<'

            for _ in range(packet_size):
                packet_data.writeByte(self.buffer.readByte())

            self._compact_buffer()
            packet_data.seek(0)

            Registry.init_global()

            stream = Stream(packet_data, self.registry)
            packet = stream.read_object()

            if packet:
                self.error_handler.log_debug(
                    f"Successfully parsed packet: {type(packet).__name__}",
                    "PACKET_PARSER"
                )
                self._handle_parsed_packet(packet)
                return True
            else:
                # We keep consuming forward even if object parse fails to avoid a buffer deadlock.
                self.error_handler.log_warning(
                    "Failed to parse packet object",
                    "PACKET_PARSER"
                )
                return True

        except Exception as e:
            self.error_handler.log_error(
                f"Error parsing packet: {e}",
                "PACKET_PARSER"
            )
            return True

    def _compact_buffer(self):
        from pyamf import amf3

        new_buffer = amf3.ByteArray()
        new_buffer.endian = '<'

        if self.buffer.remaining() > 0:
            remaining_bytes = self.buffer.read()
            new_buffer.write(remaining_bytes)

        new_buffer.seek(0)
        self.buffer = new_buffer

    def _handle_parsed_packet(self, packet):
        try:
            if not isinstance(packet, Packet):
                self.error_handler.log_debug(
                    f"Expected Packet object, got: {type(packet).__name__}",
                    "PACKET_HANDLER"
                )
                return

            if packet.packet_type == PacketType.PING:
                device_id = self.device_id or getattr(packet.message, 'device_id', 'unknown')
                device_name = self.device_name or getattr(packet.message, 'device_name', 'unknown')
                self.error_handler.log_debug(
                    f"Received ping from device: {device_name} - {device_id}",
                    "PACKET_HANDLER"
                )
                self._route_message('ping', packet.message)
                return

            if packet.message and isinstance(packet.message, BMInvoke):
                bm_invoke = packet.message

                self.error_handler.log_debug(
                    f"BMInvoke method: {bm_invoke.method}, params: {len(bm_invoke.params_list)}",
                    "PACKET_HANDLER"
                )

                self._route_message(bm_invoke.method, bm_invoke)

        except Exception as e:
            self.error_handler.log_error(
                f"Error handling parsed packet: {e}",
                "PACKET_HANDLER"
            )

    def _route_message(self, method_name: str, message):
        try:
            if method_name in self.message_handlers:
                handler = self.message_handlers[method_name]
                handler(message, self)
            else:
                self.error_handler.log_warning(
                    f"No handler for method: {method_name}",
                    "MESSAGE_ROUTER"
                )
        except Exception as e:
            self.error_handler.log_error(
                f"Error routing message {method_name}: {e}",
                "MESSAGE_ROUTER"
            )

    def send_packet(self, packet_obj: Any) -> bool:
        try:
            packet_data = self.packet_processor.create_response_packet(packet_obj)
            if packet_data:
                self.client_socket.send(packet_data)

                self.error_handler.log_info(
                    f"Sent {type(packet_obj).__name__} to {self.client_address[0]}:{self.client_address[1]}",
                    "PACKET_SENDER"
                )
                return True
            else:
                self.error_handler.log_warning(
                    f"Failed to serialize packet {type(packet_obj).__name__}",
                    "PACKET_SENDER"
                )
                return False

        except Exception as e:
            self.error_handler.handle_client_error(
                self.client_address, e, "sending packet"
            )
            return False

    def get_client_info(self) -> Dict[str, Any]:
        return {
            'address': self.client_address,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'is_running': self.is_running,
            'last_ping': self.last_ping_time
        }

    def set_device_info(self, device_id: str, device_name: str):
        self.device_id = device_id
        self.device_name = device_name

        self.error_handler.log_info(
            f"Device info set: {device_id} - {device_name}",
            "DEVICE_INFO"
        )

    def is_connected(self) -> bool:
        return self.is_running and self.client_socket and self.client_thread and self.client_thread.is_alive()