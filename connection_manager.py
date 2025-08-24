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
from typing import Dict, List, Optional, Callable, Any
from client_handler import ClientHandler
from packet_processor import PacketProcessor
from error_handler import ErrorHandler
from config import Config
from bm_protocol.registry import Registry

class ConnectionManager:
    def __init__(self, config: Config, error_handler: ErrorHandler, registry: 'Registry' = None,
                 packet_processor: 'PacketProcessor' = None, message_handlers: Dict[str, Callable] = None):
        self.config = config
        self.error_handler = error_handler
        self.registry = registry
        self.packet_processor = packet_processor or PacketProcessor(error_handler, registry)
        self.message_handlers = message_handlers or {}

        self.server_socket = None
        self.is_running = False
        self.accept_thread = None
        self._shutdown_in_progress = False

        self.clients: Dict[str, ClientHandler] = {}
        self.clients_lock = threading.Lock()

        self.on_client_connected: Optional[Callable] = None
        self.on_client_disconnected: Optional[Callable] = None

    def start(self) -> bool:
        try:
            if self.is_running:
                return True

            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(0.5)

            self.server_socket.bind((self.config.server_host, self.config.server_port))
            self.server_socket.listen(self.config.max_connections)

            self.is_running = True

            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.accept_thread.start()

            self.error_handler.log_info(
                f"Connection manager started on {self.config.server_host}:{self.config.server_port}",
                "CONNECTION_MANAGER"
            )

            return True

        except Exception as e:
            self.error_handler.handle_server_error(e, "starting connection manager")
            return False

    def stop(self):
        self.is_running = False
        self._shutdown_in_progress = True
        self._close_all_clients()

        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        if self.accept_thread and self.accept_thread.is_alive():
            self.accept_thread.join(timeout=2.0)

        self.error_handler.log_info("Connection manager stopped", "CONNECTION_MANAGER")

    def _accept_connections(self):
        while self.is_running:
            try:
                self.cleanup_disconnected_clients()
            except Exception as e:
                self.error_handler.handle_server_error(e, "cleaning up disconnected clients")

            try:
                client_socket, client_address = self.server_socket.accept()

                self.cleanup_disconnected_clients()

                with self.clients_lock:
                    if len([c for c in self.clients.values() if c.is_connected()]) >= self.config.max_connections:
                        self.error_handler.log_warning(
                            f"Connection limit reached, rejecting {client_address[0]}:{client_address[1]}",
                            "CONNECTION_MANAGER"
                        )
                        client_socket.close()
                        continue

                client_id = f"{client_address[0]}:{client_address[1]}"
                client_handler = ClientHandler(
                    client_socket=client_socket,
                    client_address=client_address,
                    packet_processor=self.packet_processor,
                    error_handler=self.error_handler,
                    registry=self.registry,
                    message_handlers=self.message_handlers.copy(),
                    on_disconnect_callback=None
                )

                if client_handler.start():
                    with self.clients_lock:
                        self.clients[client_id] = client_handler

                    self.error_handler.log_info(
                        f"New client connected: {client_address[0]}:{client_address[1]}",
                        "CONNECTION_MANAGER"
                    )

                    if self.on_client_connected:
                        try:
                            self.on_client_connected(client_handler)
                        except Exception as e:
                            self.error_handler.handle_client_error(
                                client_address, e, "client connected callback"
                            )
                else:
                    self.error_handler.log_warning(
                        f"Failed to start client handler for {client_address[0]}:{client_address[1]}",
                        "CONNECTION_MANAGER"
                    )
                    try:
                        client_socket.close()
                    except:
                        pass

            except socket.timeout:
                try:
                    self.cleanup_disconnected_clients()
                except Exception as e:
                    self.error_handler.handle_server_error(e, "cleanup after timeout")
                continue
            except socket.error as e:
                if self.is_running:
                    self.error_handler.handle_connection_error("server", e, "accepting connections")
                break
            except Exception as e:
                self.error_handler.handle_server_error(e, "accepting connections")
                break

    def _close_all_clients(self):
        with self.clients_lock:
            for client_id, client_handler in list(self.clients.items()):
                try:
                    client_handler.stop()
                except Exception as e:
                    self.error_handler.handle_client_error(
                        client_handler.client_address, e, "closing client"
                    )

            self.clients.clear()

    def get_connected_clients(self) -> List[Dict[str, Any]]:
        clients_info = []

        with self.clients_lock:
            for client_id, client_handler in self.clients.items():
                if client_handler.is_connected():
                    info = client_handler.get_client_info()
                    info['client_id'] = client_id
                    clients_info.append(info)

        return clients_info

    def get_connection_count(self) -> int:
        with self.clients_lock:
            return len([c for c in self.clients.values() if c.is_connected()])

    def cleanup_disconnected_clients(self):
        to_cleanup = []
        with self.clients_lock:
            for client_id, client_handler in list(self.clients.items()):
                if not client_handler.is_connected():
                    to_cleanup.append((client_id, client_handler))

        for client_id, client_handler in to_cleanup:
            try:
                if not getattr(client_handler, "_server_cleanup_done", False):
                    if self.on_client_disconnected:
                        self.on_client_disconnected(client_handler)
                    setattr(client_handler, "_server_cleanup_done", True)
            except Exception as e:
                self.error_handler.handle_client_error(
                    client_handler.client_address, e, "client disconnected callback"
                )

        with self.clients_lock:
            for client_id, _ in to_cleanup:
                self.clients.pop(client_id, None)
                self.error_handler.log_info(f"Cleaned up disconnected client: {client_id}", "CONNECTION_MANAGER")

    def get_client_by_device_id(self, device_id: str) -> Optional[ClientHandler]:
        with self.clients_lock:
            for client_handler in self.clients.values():
                if hasattr(client_handler, 'device_id') and client_handler.device_id == device_id:
                    return client_handler

        return None

    def set_connection_callbacks(self, on_connected: Callable = None, on_disconnected: Callable = None):
        self.on_client_connected = on_connected
        self.on_client_disconnected = on_disconnected
