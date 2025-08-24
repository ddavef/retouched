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

import subprocess, sys, time, socket
from pathlib import Path

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception:
            return "localhost"

def start_servers():
    project_root = Path(__file__).parent

    local_ip = get_local_ip()

    processes = []

    argv = sys.argv[1:]
    debug_enabled = any(arg in ("-d", "--debug", "-debug") for arg in argv)
    forward_flags = ["-d"] if debug_enabled else []

    try:
        print("Starting Registry Server (port 8088)...")
        registry_process = subprocess.Popen([
            sys.executable, "run_server.py", *forward_flags
        ], cwd=project_root, stdin=subprocess.PIPE, text=True)

        registry_process.stdin.write("n\n")
        registry_process.stdin.flush()

        processes.append(registry_process)
        time.sleep(3)

        print("\nAll servers started!")
        print(f"Registry Server: {local_ip}:8088 (for Flash clients)")
        print("Press Ctrl+C to stop all servers")

        for process in processes:
            process.wait()

    except KeyboardInterrupt:
        print("\nShutting down servers...")
        for process in processes:
            process.terminate()

        time.sleep(2)

        for process in processes:
            if process.poll() is None:
                process.kill()

        print("All servers stopped.")

if __name__ == "__main__":
    start_servers()