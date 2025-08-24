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

from typing import Any, Dict

HOST = "0.0.0.0"
PORT = 8088

_ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}

class Config:
    def __init__(self):
        self.http_port = 8080

        self.max_connections = 100
        self.socket_timeout = 30.0
        self.buffer_size = 4096
        self.max_packet_size = 1024 * 1024  # 1 MiB

        self.log_level = "INFO"
        self.log_to_file = False
        self.log_file_path = "server.log"
        self.log_max_size = 10 * 1024 * 1024  # 10MB
        self.log_backup_count = 5

        self.debug = False
        self.verbose_logging = False

        self.thread_pool_size = 10
        self.packet_queue_size = 100

    @property
    def server_host(self) -> str:
        return HOST

    @server_host.setter
    def server_host(self, _value: str):
        return

    @property
    def server_port(self) -> int:
        return PORT

    @server_port.setter
    def server_port(self, _value: int):
        return

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        cfg = cls()
        try:
            import json
            with open(config_path, "r") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                print(f"Config file must contain a JSON object, got: {type(data).__name__}")
                return cfg

            mutable_keys = {
                "http_port",
                "max_connections",
                "socket_timeout",
                "buffer_size",
                "log_level",
                "log_to_file",
                "log_file_path",
                "log_max_size",
                "log_backup_count",
                "verbose_logging",
                "thread_pool_size",
                "packet_queue_size",
                "allow_anonymous_connections",
                "max_packet_size",
            }

            for key, value in data.items():
                if key in ("server_host", "server_port"):
                    continue
                if key not in mutable_keys:
                    continue
                try:
                    setattr(cfg, key, value)
                except Exception:
                    pass

        except FileNotFoundError:
            print(f"Config file not found: {config_path}, using defaults")
        except Exception as e:
            print(f"Error loading config '{config_path}': {e}, using defaults")

        cfg._normalize()
        return cfg

    def to_dict(self) -> Dict[str, Any]:
        return {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "http_port": self.http_port,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "buffer_size": self.buffer_size,
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_file_path": self.log_file_path,
            "log_max_size": self.log_max_size,
            "log_backup_count": self.log_backup_count,
            "debug": self.debug,
            "verbose_logging": self.verbose_logging,
            "thread_pool_size": self.thread_pool_size,
            "packet_queue_size": self.packet_queue_size,
            "max_packet_size": self.max_packet_size,
        }

    def save_to_file(self, config_path: str):
        try:
            import json
            with open(config_path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def _normalize(self):
        try:
            self.max_connections = int(self.max_connections)
        except Exception:
            self.max_connections = 100

        try:
            self.http_port = int(self.http_port)
        except Exception:
            self.http_port = 8080

        try:
            self.socket_timeout = float(self.socket_timeout)
        except Exception:
            self.socket_timeout = 30.0

        try:
            self.buffer_size = int(self.buffer_size)
        except Exception:
            self.buffer_size = 4096

        try:
            self.log_max_size = int(self.log_max_size)
        except Exception:
            self.log_max_size = 10 * 1024 * 1024

        try:
            self.log_backup_count = int(self.log_backup_count)
        except Exception:
            self.log_backup_count = 5

        try:
            self.thread_pool_size = int(self.thread_pool_size)
        except Exception:
            self.thread_pool_size = 10

        try:
            self.packet_queue_size = int(self.packet_queue_size)
        except Exception:
            self.packet_queue_size = 100

        try:
            self.max_packet_size = int(self.max_packet_size)
        except Exception:
            self.max_packet_size = 1024 * 1024

        self.log_to_file = bool(self.log_to_file)
        self.debug = bool(self.debug)
        self.verbose_logging = bool(self.verbose_logging)

        self.log_file_path = str(self.log_file_path) if self.log_file_path is not None else "server.log"

        lvl = str(self.log_level).upper() if self.log_level is not None else "INFO"
        self.log_level = lvl if lvl in _ALLOWED_LOG_LEVELS else "INFO"
        if self.log_level == "DEBUG" and not bool(self.debug):
            self.log_level = "INFO"

    def validate(self) -> bool:
        if not (1 <= self.server_port <= 65535):
            print(f"Invalid fixed port: {self.server_port}")
            return False
        if not (1 <= self.http_port <= 65535):
            print(f"Invalid http_port: {self.http_port}")
            return False

        if self.max_connections < 1:
            print(f"Invalid max_connections: {self.max_connections}")
            return False
        if self.thread_pool_size < 1:
            print(f"Invalid thread_pool_size: {self.thread_pool_size}")
            return False
        if self.packet_queue_size < 1:
            print(f"Invalid packet_queue_size: {self.packet_queue_size}")
            return False
        if self.buffer_size < 512:
            print(f"buffer_size too small: {self.buffer_size}")
            return False
        if self.max_packet_size < 1024:
            print(f"max_packet_size too small: {self.max_packet_size}")
            return False

        if self.socket_timeout < 0.0:
            print(f"Invalid socket_timeout: {self.socket_timeout}")
            return False

        if self.log_level not in _ALLOWED_LOG_LEVELS:
            print(f"Invalid log_level: {self.log_level}")
            return False

        return True

    def __str__(self) -> str:
        return f"Config(host={self.server_host}, port={self.server_port}, max_conn={self.max_connections})"