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

from pyamf import amf3

class BMRegistryInfo:
    def __init__(self):
        self._slot_id = 0
        self._app_id = ""
        self._max_clients = 0
        self._current_clients = 0
        self._device = None
        self._address = None

    @property
    def max_clients(self):
        return self._max_clients

    @max_clients.setter
    def max_clients(self, value):
        self._max_clients = value

    @property
    def current_clients(self):
        return self._current_clients

    @current_clients.setter
    def current_clients(self, value):
        self._current_clients = value

    @property
    def slot_id(self):
        return self._slot_id

    @slot_id.setter
    def slot_id(self, value):
        self._slot_id = value

    @property
    def app_id(self):
        return self._app_id

    @app_id.setter
    def app_id(self, value: str):
        self._app_id = value

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    def read_external(self, data_input: amf3.DataInput):
        self._device = data_input.readObject()
        self._address = data_input.readObject()
        self._device.address = self._address
        self._app_id = data_input.readUTF()
        self._slot_id = data_input.readShort()
        if self._slot_id > 0:
            self._current_clients = data_input.readShort()
            self._max_clients = data_input.readShort()

    def write_external(self, data_output):
        if hasattr(data_output, 'write_object'):
            data_output.write_object(self._device)
            if self._address is not None:
                data_output.write_object(self._address)
                data_output.write_utf(self._app_id)
                data_output.write_short(self._slot_id)
                if self._slot_id > 0:
                    data_output.write_short(self._current_clients)
                    data_output.write_short(self._max_clients)
            else:
                raise Exception("Address is None")
        else:
            data_output.writeObject(self._device)
            if self._address is not None:
                data_output.writeObject(self._address)
                data_output.writeUTF(self._app_id)
                data_output.writeShort(self._slot_id)
                if self._slot_id > 0:
                    data_output.writeShort(self._current_clients)
                    data_output.writeShort(self._max_clients)
            else:
                raise Exception("Address is None")

    def __str__(self):
        return (f"BMRegistryInfo(slot_id={self._slot_id}, app_id={self._app_id}, "
                f"max_clients={self._max_clients}, current_clients={self._current_clients}, "
                f"device={self._device}, address={self._address})")