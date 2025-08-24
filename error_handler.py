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

import traceback
import logging
from typing import Any
from datetime import datetime

DEBUG_ENABLED = False

def set_debug_enabled(enabled: bool):
    global DEBUG_ENABLED
    DEBUG_ENABLED = bool(enabled)

class ErrorHandler:
    def __init__(self, log_to_file: bool = True, log_file: str = "server_errors.log"):
        self.log_to_file = log_to_file
        self.log_file = log_file

        if log_to_file:
            logging.basicConfig(
                filename=log_file,
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

    def _log_message(self, level: str, message: str, context: str = "GENERAL"):
        if level == "DEBUG" and not DEBUG_ENABLED:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {context}: {message}"

        print(formatted_message, flush=True)

        if self.log_to_file:
            if level == "ERROR":
                logging.error(f"{context}: {message}")
            elif level == "WARNING":
                logging.warning(f"{context}: {message}")
            elif level == "INFO":
                logging.info(f"{context}: {message}")
            elif level == "DEBUG":
                logging.debug(f"{context}: {message}")

    def handle_client_error(self, client_addr: tuple, error: Exception, context: str = ""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        client_str = f"{client_addr[0]}:{client_addr[1]}"

        error_msg = f"[{timestamp}] [{client_str}] Error in {context}: {error}"

        print(error_msg, flush=True)

        if self.log_to_file:
            logging.error(f"[{client_str}] Error in {context}: {error}")
            logging.error(f"Traceback: {traceback.format_exc()}")

        if hasattr(error, '__traceback__'):
            traceback.print_exc()

    def handle_server_error(self, error: Exception, context: str = ""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error_msg = f"[{timestamp}] [SERVER] Error in {context}: {error}"

        print(error_msg, flush=True)

        if self.log_to_file:
            logging.error(f"[SERVER] Error in {context}: {error}")
            logging.error(f"Traceback: {traceback.format_exc()}")

        if hasattr(error, '__traceback__'):
            traceback.print_exc()

    def handle_packet_error(self, packet_data: Any, error: Exception, context: str = ""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error_msg = f"[{timestamp}] [PACKET] Error in {context}: {error}"

        print(error_msg, flush=True)

        if self.log_to_file:
            logging.error(f"[PACKET] Error in {context}: {error}")
            logging.error(f"Packet data type: {type(packet_data)}")
            logging.error(f"Traceback: {traceback.format_exc()}")

    def handle_connection_error(self, client_ip: str, error: Exception, context: str = ""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error_msg = f"[{timestamp}] [CONNECTION] [{client_ip}] Error in {context}: {error}"

        print(error_msg, flush=True)

        if self.log_to_file:
            logging.error(f"[CONNECTION] [{client_ip}] Error in {context}: {error}")

    def log_error(self, message: str, context: str = "GENERAL"):
        self._log_message("ERROR", message, context)

    def log_warning(self, message: str, context: str = "GENERAL"):
        self._log_message("WARNING", message, context)

    def log_info(self, message: str, context: str = "GENERAL"):
        self._log_message("INFO", message, context)

    def log_debug(self, message: str, context: str = "GENERAL"):
        self._log_message("DEBUG", message, context)

    @staticmethod
    def is_critical_error(error: Exception) -> bool:
        critical_errors = (
            OSError,
            MemoryError,
            SystemExit,
            KeyboardInterrupt
        )

        return isinstance(error, critical_errors)