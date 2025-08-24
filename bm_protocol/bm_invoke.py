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

from .bm_parameter import BMParameter

class BMInvoke:
    SOURCE = None

    def __init__(self, iid=0, method="", *args):
        self.id = iid
        self.method = method
        self.params_list = []
        self.return_method = ""

        for arg in args:
            self.add_parameter(BMParameter(arg))

    def add_parameter(self, parameter):
        self.params_list.append(parameter)

    def get_return_method(self):
        return self.return_method

    def get_params(self):
        return self.params_list

    def get_method_name(self):
        return self.method

    def set_return_method(self, method):
        self.return_method = method

    def read_external(self, data_input):
        self.id = data_input.readInt()
        self.method = data_input.readUTF()
        self.return_method = data_input.readUTF()
        num_params = data_input.readInt()
        self.params_list = []

        if num_params > 0:
            for i in range(num_params):
                param = data_input.readObject()
                self.params_list.append(param)

    def write_external(self, data_output):
        if hasattr(data_output, 'write_int'):
            data_output.write_int(self.id)
            data_output.write_utf(self.method or "")
            data_output.write_utf(self.return_method or "")
            data_output.write_int(len(self.params_list))
            for param in self.params_list:
                data_output.write_object(param)
        else:  # DataOutput object
            data_output.writeInt(self.id)
            data_output.writeUTF(self.method or "")
            data_output.writeUTF(self.return_method or "")
            data_output.writeInt(len(self.params_list))
            for param in self.params_list:
                data_output.writeObject(param)