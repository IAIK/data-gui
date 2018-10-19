"""
Copyright (C) 2018 IAIK TU Graz (data@iaik.tugraz.at)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

@version 1.1

"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem

from datagui.package.utils import CustomRole


class BaseTreeItem(QStandardItem):
    def __init__(self, name, obj=None, parent=None):
        super(BaseTreeItem, self).__init__()
        self.parent_item = parent
        self.name = name
        self.obj = obj
        self.child_items = []

    def appendChild(self, item):
        self.child_items.append(item)

    def childCount(self):
        return len(self.child_items)

    def data(self, role, column=0):
        if role == Qt.DisplayRole:
            try:
                return self.name
            except IndexError:
                return None
        elif role == CustomRole.Obj:
            return self.obj
        elif role == CustomRole.Ip:
            return self.obj.ip
        else:
            return None

    def parent(self):
        return self.parent_item

    def row(self):
        if self.parent_item:
            return self.parent_item.child_items.index(self)

        return 0
