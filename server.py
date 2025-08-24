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

import threading, time
from typing import Dict, Any, Optional
from connection_manager import ConnectionManager
from packet_processor import PacketProcessor
from error_handler import ErrorHandler
from config import Config
from client_handler import ClientHandler
from bm_protocol.registry import Registry
from bm_protocol.bm_invoke import BMInvoke
from bm_protocol.bm_parameter import BMParameter
from bm_protocol.bm_array import BMArray
from bm_protocol.device_type import DeviceType
from bm_protocol.packet import Packet
from bm_protocol.packet_type import PacketType
from http_server import BMRegistryHTTPServer
from packet_operations_mixin import PacketOperationsMixin

class Server(PacketOperationsMixin):
    def __init__(self, config: Config):
        PacketOperationsMixin.__init__(self)
        self.config = config
        self.error_handler = ErrorHandler(
            log_to_file=config.log_to_file,
            log_file=config.log_file_path
        )
        self.registry = Registry(self.error_handler)
        self.registry.init()
        self.allocated_slots = set()
        self._slot_lock = threading.Lock()
        self.packet_processor = PacketProcessor(self.error_handler, self.registry)

        self._setup_message_handlers()

        self.connection_manager = ConnectionManager(
            config,
            self.error_handler,
            self.registry,
            self.packet_processor,
            self.message_handlers
        )

        self.is_running = False
        self.start_time = None
        self._shutdown_in_progress = False

        import random
        import string
        characters = string.ascii_lowercase + string.digits
        self.server_device_id = ''.join(random.choices(characters, k=69))

        self.connection_manager.set_connection_callbacks(
            on_connected=self._on_client_connected,
            on_disconnected=self._on_client_disconnected
        )

        self.http_server = BMRegistryHTTPServer(
            host=config.server_host,
            port=config.http_port
        )

    def start(self) -> bool:
        if self.is_running:
            return True

        self.is_running = True
        self.start_time = time.time()

        if self.connection_manager.start():
            self.http_server.start()
            self.error_handler.log_info("Server started successfully (TCP + HTTP)", "SERVER")
            return True
        else:
            self.is_running = False
            return False

    def stop(self):
        if not self.is_running:
            return

        self._shutdown_in_progress = True
        self.is_running = False

        self.connection_manager.stop()
        self.http_server.stop()

        self.error_handler.log_info("Server stopped (TCP + HTTP)", "SERVER")

    def _setup_message_handlers(self):
        self.message_handlers = {
            'registry.register': self.on_registry_register,
            'registry.list': self.on_registry_list,
            'registry.relay': self.on_registry_relay,
            'registry.update': self.on_registry_update,
            'ping': self.on_ping
        }

    def on_registry_register(self, inv_message: BMInvoke, client_handler: ClientHandler):
        """
        Handles the registry.register message from a client.
        The registration packet contains the information from a client after the handshake is complete.
        Example: device id, device name, device type, etc.
        Flash/unity clients expect an onHostConnected message after the registration packet is received with the calculated slot id.
        Sends a registration packet from the server itself for Touchy to progress.
        """
        self.error_handler.log_info(f"Processing registry.register from {client_handler.client_address}", "REGISTRY")
        try:
            if not inv_message.params_list or not inv_message.params_list[0].value:
                self.error_handler.log_error("No parameters in registry.register call", "REGISTRY")
                return

            client_info = inv_message.params_list[0].value
            if not hasattr(client_info, "device") or not client_info.device:
                self.error_handler.log_error("No device info in registry call", "REGISTRY")
                return

            device_id = getattr(client_info.device, "device_id", "unknown")
            device_name = getattr(client_info.device, "device_name", "unknown")
            device_type = getattr(client_info.device, "device_type", None)

            if device_type in (DeviceType.FLASH, DeviceType.UNITY):
                allocated_slot_id = self.allocate_slot_id()
                client_info.slot_id = allocated_slot_id
                client_handler.slot_id = allocated_slot_id
                self.error_handler.log_info(f"Allocated slot {allocated_slot_id} to [{device_type}] client", "REGISTRY")
            else:
                client_info.slot_id = 0
                client_handler.slot_id = 0

            try:
                client_handler.set_device_info(device_id, device_name)
            except Exception:
                pass
            client_handler.client_info = client_info

            try:
                self.registry.unregister_device(device_id)
            except Exception:
                pass
            self.registry.register_device(client_info)

            self.error_handler.log_info(
                f"Device registered: {device_name} ({device_id}), Slot: {getattr(client_info, 'slot_id', 'N/A')}",
                "REGISTRY"
            )

            # Doing this will make Touchy progress to showing the list of games
            client_handler.send_registration_response(
                original_invoke=inv_message,
                server_device_id=self.server_device_id,
                server_host=self.config.server_host,
                server_port=self.config.server_port
            )

            # For flash/unity clients, we need to send onHostConnected to update the slot color
            if device_type in (DeviceType.FLASH, DeviceType.UNITY):
                client_handler.notify_host_connected()

            self._send_filtered_device_list(client_handler, device_type)
            self._broadcast_device_list_update(client_handler)

        except Exception as e:
            self.error_handler.log_error(f"Error in registry.register: {e}", "REGISTRY")

    def on_registry_list(self, invoke: BMInvoke, client_handler: ClientHandler):
        try:
            device_type = None
            if hasattr(client_handler, 'client_info') and client_handler.client_info:
                if hasattr(client_handler.client_info, 'device') and client_handler.client_info.device:
                    device_type = client_handler.client_info.device.device_type

            self._send_filtered_device_list(client_handler, device_type)
        except Exception as e:
            self.error_handler.log_error(f"Error handling registry.list: {e}", "REGISTRY")

    def on_registry_relay(self, inv_message: BMInvoke, client_handler: ClientHandler):
        """
        Relays a message from one device to another.
        Controller apps send this message to the server that it needs to relay to the games.
        """
        self.error_handler.log_info(f"Processing registry.relay from {client_handler.client_address}", "REGISTRY")

        try:
            if len(inv_message.params_list) < 2:
                self.error_handler.log_warning("Invalid relay request - need 2 parameters", "REGISTRY")
                return

            target_info = inv_message.params_list[0].value
            relay_message = inv_message.params_list[1].value

            if not hasattr(target_info, 'device') or not target_info.device:
                self.error_handler.log_warning("Invalid target info in relay", "REGISTRY")
                return

            target_device_id = getattr(target_info.device, 'device_id', None)
            if not target_device_id:
                self.error_handler.log_warning("No device ID in target info", "REGISTRY")
                return

            self.error_handler.log_info(f"Relaying message to device: {target_device_id}", "REGISTRY")

            target_client = self.connection_manager.get_client_by_device_id(target_device_id)
            if not target_client:
                self.error_handler.log_warning(f"Target device {target_device_id} not found", "REGISTRY")
                return

            try:
                sender_type = None
                if getattr(client_handler, "client_info", None) and getattr(client_handler.client_info, "device", None):
                    sender_type = getattr(client_handler.client_info.device, "device_type", None)

                if sender_type not in [DeviceType.FLASH, DeviceType.UNITY]:
                    target_slot = int(getattr(target_client, "slot_id", 0) or 0)
                    already_paired = (getattr(client_handler, "paired_slot_id", None) == target_slot)

                    if target_slot:
                        try:
                            live_count = getattr(getattr(target_client, "client_info", None), "current_clients", 0)
                            live_count = int(live_count if live_count is not None else 0)
                        except Exception:
                            live_count = 0

                        try:
                            max_clients = int(
                                getattr(getattr(target_client, "client_info", None), "max_clients", 1) or 1
                            )
                        except Exception:
                            max_clients = 1

                        if live_count >= max_clients and not already_paired:
                            self.error_handler.log_warning(
                                f"Relay blocked: game slot {target_slot} is full ({live_count}/{max_clients})",
                                "REGISTRY"
                            )
                            return
            except Exception as e:
                self.error_handler.log_warning(f"relay capacity check skipped: {e}", "REGISTRY")

            relay_packet = self._create_relay_packet(client_handler, relay_message)

            if target_client.send_packet(relay_packet):
                self.error_handler.log_info(
                    f"Successfully relayed message from {relay_packet.device_id} to {target_device_id}",
                    "REGISTRY"
                )
            else:
                self.error_handler.log_error(
                    f"Failed to send relayed message to {target_device_id}",
                    "REGISTRY"
                )

        except Exception as e:
            self.error_handler.log_error(f"Error in registry.relay: {e}", "REGISTRY")

    def on_registry_update(self, inv_message: BMInvoke, client_handler: ClientHandler):
        try:
            info = inv_message.params_list[0].value if inv_message.params_list else None

            if getattr(client_handler, "client_info", None) is not None and info is not None:
                if hasattr(info, "max_clients"):
                    try:
                        client_handler.client_info.max_clients = int(getattr(info, "max_clients", 0) or 0)
                    except Exception:
                        pass

                if hasattr(info, "current_clients"):
                    try:
                        val = getattr(info, "current_clients", None)
                        if val is not None:
                            client_handler.client_info.current_clients = int(val)
                    except Exception:
                        pass

                if hasattr(info, "slot_id"):
                    try:
                        sid = int(getattr(info, "slot_id", 0) or 0)
                        if sid:
                            client_handler.client_info.slot_id = sid
                            client_handler.slot_id = sid
                    except Exception:
                        pass

            try:
                self._broadcast_device_list_update(None)
            except Exception:
                pass

            return_method = getattr(inv_message, 'return_method', None) or "onRegister"
            response = BMInvoke(iid=inv_message.id, method=return_method)

            ok = BMParameter(True)
            ok.encoding = "2"
            response.add_parameter(ok)

            packet = Packet()
            packet.message = response
            client_handler.send_packet(packet)

        except Exception as e:
            self.error_handler.log_error(f"Error handling registry.update: {e}", "REGISTRY")

    def on_ping(self, *args):
        client_handler = args[-1] if args else None

        if not client_handler:
            self.error_handler.log_error("No client handler provided to ping", "PING")
            return

        try:
            self.error_handler.log_debug(f"Received ping from {client_handler.client_address}", "PING")

            success = self.send_ping_response_to_socket(
                client_handler.client_socket,
                self.server_device_id,
                self.config.server_host or "127.0.0.1",
                self.config.server_port
            )

            if not success:
                self.error_handler.log_error("Failed to send ping response", "PING")

        except Exception as e:
            self.error_handler.log_error(f"Error handling ping: {e}", "PING")

    def _send_filtered_device_list(self, client_handler: ClientHandler, device_type):
        """
        Sends a filtered list of devices to the client based on the device type.
        Flash/unity clients are sent the complete list of devices.
        Android/iPhone clients are only sent flash/unity devices.
        """
        from copy import deepcopy
        try:
            viewer_is_game = device_type in [DeviceType.FLASH, DeviceType.UNITY]
            with self.connection_manager.clients_lock:
                clients_snapshot = dict(self.connection_manager.clients)

            all_devices = self.registry.get_all_devices()
            filtered_devices = []
            seen_ids = set()

            for dev in all_devices:
                d_obj = getattr(dev, "device", None) or dev
                d_id = getattr(d_obj, "device_id", None)
                d_type = getattr(d_obj, "device_type", None)
                if not d_id or d_type is None:
                    continue
                if d_id in seen_ids:
                    continue

                include = True if viewer_is_game else (d_type in [DeviceType.FLASH, DeviceType.UNITY])
                if not include:
                    continue

                device_client = None
                for ch in clients_snapshot.values():
                    if getattr(ch, "device_id", None) == d_id and ch.is_connected():
                        device_client = ch
                        break
                if not device_client:
                    continue

                slot_for_emit = 0
                current_clients = None
                max_clients = None

                if d_type in [DeviceType.FLASH, DeviceType.UNITY]:
                    try:
                        slot_for_emit = int(getattr(device_client, "slot_id", 0) or 0)
                    except Exception:
                        slot_for_emit = 0
                    try:
                        ci = getattr(device_client, "client_info", None)
                        current_clients = int(getattr(ci, "current_clients", 0) or 0) if ci else 0
                    except Exception:
                        current_clients = 0
                    try:
                        ci = getattr(device_client, "client_info", None)
                        max_clients = int(getattr(ci, "max_clients", 0) or 0) if ci else 0
                    except Exception:
                        max_clients = 0

                try:
                    dev_copy = deepcopy(dev)
                except Exception:
                    dev_copy = dev
                    slot_for_emit = 0
                    current_clients = None
                    max_clients = None

                try:
                    target_obj = getattr(dev_copy, "device", None) or dev_copy
                    if slot_for_emit:
                        setattr(dev_copy, "slot_id", slot_for_emit)
                        if hasattr(target_obj, "slot_id"):
                            setattr(target_obj, "slot_id", slot_for_emit)
                    if current_clients is not None:
                        setattr(dev_copy, "current_clients", current_clients)
                    if max_clients is not None and max_clients >= 0:
                        setattr(dev_copy, "max_clients", max_clients)
                except Exception:
                    pass

                filtered_devices.append(dev_copy)
                seen_ids.add(d_id)
                self.error_handler.log_debug(f"List include: {d_id} -> slot {slot_for_emit}", "REGISTRY")

            device_array = BMArray(*filtered_devices)
            params = [BMParameter(device_array)]

            success = client_handler.send_invoke_packet(
                method="onList",
                params=params,
                sequence=2,
                device_id=self.server_device_id,
                device_name="Registry",
                packet_type=PacketType.DATA,
                device_type=DeviceType.SERVER
            )

            if success:
                who = "game" if viewer_is_game else "app"
                self.error_handler.log_info(f"Sent filtered device list to {who}", "REGISTRY")
        except Exception as e:
            self.error_handler.log_error(f"Error sending device list: {e}", "REGISTRY")

    def _create_relay_packet(self, sender_client: ClientHandler, relay_message: BMInvoke) -> Packet:
        sender_device_id = self.server_device_id
        sender_device_name = "Registry"
        sender_device_type = DeviceType.SERVER

        if hasattr(sender_client, 'client_info') and sender_client.client_info:
            if hasattr(sender_client.client_info, 'device') and sender_client.client_info.device:
                sender_device_type = getattr(sender_client.client_info.device, 'device_type', DeviceType.FLASH)
                sender_device_id = getattr(sender_client.client_info.device, 'device_id', 'unknown')
                sender_device_name = getattr(sender_client.client_info.device, 'device_name', 'unknown')

        return self.create_relay_packet_common(
            sender_device_id, sender_device_name, sender_device_type,
            relay_message, self.server_device_id
        )

    def _broadcast_device_list_update(self, newly_connected_client: Optional[ClientHandler]):
        try:
            with self.connection_manager.clients_lock:
                targets = list(self.connection_manager.clients.values())

            for ch in targets:
                if not ch.is_connected():
                    continue
                dtype = None
                try:
                    if getattr(ch, "client_info", None) and getattr(ch.client_info, "device", None):
                        dtype = getattr(ch.client_info.device, "device_type", None)
                except Exception:
                    dtype = None
                try:
                    self._send_filtered_device_list(ch, dtype)
                except Exception as e:
                    self.error_handler.log_warning(f"Broadcast list to {ch.client_address} failed: {e}", "REGISTRY")
        except Exception as e:
            self.error_handler.log_error(f"Broadcast device list error: {e}", "REGISTRY")

    def _delayed_device_list_broadcast(self):
        """
        Broadcasts the device list to all clients after a short delay.
        The delay lets app UIs properly reflect the slot colors and player counts.
        """
        if self._shutdown_in_progress or not self.is_running:
            return

        try:
            with self.connection_manager.clients_lock:
                all_clients = list(self.connection_manager.clients.values())

            broadcast_count = 0
            for client in all_clients:
                if client.is_connected():
                    client_device_type = None
                    if hasattr(client, 'client_info') and client.client_info:
                        if hasattr(client.client_info, 'device') and client.client_info.device:
                            client_device_type = getattr(client.client_info.device, 'device_type', None)

                    if client_device_type is not None:
                        self._send_filtered_device_list(client, client_device_type)
                        broadcast_count += 1

            if broadcast_count > 0:
                self.error_handler.log_info(
                    f"Broadcasted device list update to {broadcast_count} clients after disconnect", "REGISTRY"
                )

        except Exception as e:
            self.error_handler.log_error(f"Error in delayed device list broadcast: {e}", "REGISTRY")

    def allocate_slot_id(self) -> int:
        try:
            with self._slot_lock:
                sid = 1
                while sid in self.allocated_slots:
                    sid += 1
                self.allocated_slots.add(sid)
                return sid
        except Exception as e:
            self.error_handler.log_error(f"allocate_slot_id failed: {e}", "REGISTRY")
            return 0

    def free_slot_id(self, slot_id: int):
        if not slot_id:
            return
        try:
            with self._slot_lock:
                if slot_id in self.allocated_slots:
                    self.allocated_slots.remove(slot_id)
                    self.error_handler.log_info(f"Freed slot {slot_id}", "REGISTRY")
        except Exception as e:
            self.error_handler.log_error(f"free_slot_id failed: {e}", "REGISTRY")

    def _on_client_connected(self, client_handler: ClientHandler):
        self.error_handler.log_info(f"Client connected: {client_handler.client_address}", "CONNECTION")

    def _on_client_disconnected(self, client_handler: ClientHandler):
        try:
            sid = int(getattr(client_handler, "slot_id", 0) or 0)
            if sid > 0:
                self.free_slot_id(sid)

            did = getattr(client_handler, "device_id", None)
            if did:
                try:
                    self.registry.unregister_device(did)
                except Exception as e:
                    self.error_handler.log_warning(f"unregister_device failed for {did}: {e}", "REGISTRY")

            try:
                self._broadcast_device_list_update(None)
            except Exception:
                pass

            self.error_handler.log_info(f"Client disconnected: {client_handler.client_address}", "CONNECTION")
        except Exception as e:
            self.error_handler.log_error(f"Error handling client disconnect: {e}", "SERVER")

    def cleanup_disconnected_clients(self):
        self.connection_manager.cleanup_disconnected_clients()

    def get_connected_clients_info(self) -> list:
        return self.connection_manager.get_connected_clients()