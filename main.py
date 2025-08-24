#!/usr/bin/env python3

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

import sys
import signal
import threading
import argparse
from pathlib import Path
from config import Config
from server import Server

HOST = "0.0.0.0"
PORT = 8088

class Application:
    def __init__(self):
        self.server = None
        self.config = None
        self.is_shutdown = False
        self.shutdown_event = threading.Event()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        print(f"\nReceived signal {signum}, initiating graceful shutdown...")
        self.shutdown()

    def load_config(self, config_path: str = None) -> bool:
        try:
            if config_path and Path(config_path).exists():
                self.config = Config.from_file(config_path)
                print(f"Loaded configuration from: {config_path}")
            else:
                self.config = Config()
                print("Using default configuration")

            self.config.server_host = HOST
            self.config.server_port = PORT
            print(f"Using fixed endpoint: {HOST}:{PORT}")

            return True

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def start_server(self) -> bool:
        try:
            if not self.config:
                print("No configuration loaded")
                return False

            self.config.server_host = HOST
            self.config.server_port = PORT

            self.server = Server(self.config)

            if not self.server.start():
                print("Failed to start server")
                return False

            print(f"Server started successfully!")
            print(f"Listening on {self.config.server_host}:{self.config.server_port}")
            print(f"Max connections: {self.config.max_connections}")
            print(f"Debug mode: {'ON' if self.config.debug else 'OFF'}")
            print("Press Ctrl+C to stop the server")

            return True

        except FileNotFoundError as e:
            print(f"Error starting server: Directory not found: {e.filename}")
            return False
        except Exception as e:
            print(f"Error starting server: {e}")
            return False

    def run(self) -> int:
        try:
            if not self.start_server():
                return 1

            while not self.is_shutdown:
                try:
                    self._perform_maintenance()

                    if self.shutdown_event.wait(timeout=30.0):
                        break

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error in main loop: {e}")

            return 0

        except Exception as e:
            print(f"Critical error in application: {e}")
            return 1
        finally:
            self.shutdown()

    def _perform_maintenance(self):
        if self.server:
            self.server.cleanup_disconnected_clients()

    def shutdown(self):
        if self.is_shutdown:
            return

        print("Shutting down server...")
        self.is_shutdown = True
        self.shutdown_event.set()

        if self.server:
            self.server.stop()
            print("Server stopped")

def create_argument_parser():
    parser = argparse.ArgumentParser(
        description="Server Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Start with fixed endpoint (0.0.0.0:8088)
  python main.py --config server.conf      # Start with custom config file
  python main.py --debug                   # Enable debug mode
        """
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )

    parser.add_argument(
        '--max-connections',
        type=int,
        help='Maximum number of concurrent connections (overrides config)'
    )

    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Enable debug mode (overrides config)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set log level (overrides config)'
    )

    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Server Application 1.0.0'
    )

    return parser


def main():
    parser = create_argument_parser()
    args = parser.parse_args()

    app = Application()

    if not app.load_config(args.config):
        print("Failed to load configuration")
        return 1

    if args.max_connections:
        app.config.max_connections = args.max_connections
    if args.debug:
        app.config.debug = True
    if args.log_level:
        app.config.log_level = args.log_level

    try:
        return app.run()

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())