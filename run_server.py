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
from main import Application
from error_handler import set_debug_enabled

HOST = "0.0.0.0"
PORT = 8088

def main():
    print("retouched Server 1.0")
    print("==================")

    argv = sys.argv[1:]
    debug_enabled = any(arg in ("-d", "--debug", "-debug") for arg in argv)
    set_debug_enabled(debug_enabled)

    app = Application()

    if not app.load_config():
        print("Failed to load configuration")
        return 1

    if debug_enabled:
        app.config.debug = True
        app.config.log_level = "DEBUG"

    app.config.server_host = HOST
    app.config.server_port = PORT

    print(f"Starting server on {HOST}:{PORT}\n")
    return app.run()

if __name__ == "__main__":
    sys.exit(main())