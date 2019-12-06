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

@version 1.2

"""

from PyQt5.QtCore import QModelIndex, Qt, QVariant
from PyQt5.QtGui import QStandardItem

from datagui.package.model.BaseTreeModel import BaseTreeModel
from datagui.package.utils import CustomRole, CustomType, getIconById


class LeakItem(QStandardItem):
    def __init__(self, name, leak=None, parent=None):
        super(LeakItem, self).__init__()
        self.name = name
        self.leak = leak
        self.parent_item = parent
        self.high_prio_flag = -1

    def type(self):
        return CustomType.leakItem

    def parent(self):
        return self.parent_item


class LeakModel(BaseTreeModel):
    def __init__(self):
        super(LeakModel, self).__init__()
        self.header = "Leaks"
        self.none_item = LeakItem("No leaks to display", None)
        self.items = []

    # # # # # # # # # # # # #
    # OVERLOADED FUNCTIONS  #
    # # # # # # # # # # # # #

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if len(self.items) == 0:
            # We're empty. Display none_item
            item = self.none_item
        else:
            item = self.items[index.row()]

        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            return item.name
        elif role == CustomRole.Leak:
            if item.leak is not None:
                return item.leak
        elif role == CustomRole.Ip:
            if item.leak is not None:
                return item.leak.ip
        elif role == Qt.DecorationRole:
            return getIconById(item.high_prio_flag)
        return QVariant()

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if len(self.items) == 0:
            # We're empty. Display none_item
            item = self.none_item
        else:
            item = self.items[row]
        if item:
            return self.createIndex(row, column, item)
        else:
            return QModelIndex()

    def rowCount(self, parent):
        if parent.isValid():
            return 0
        if len(self.items) == 0:
            # We're empty. Display none_item
            return 1
        return len(self.items)

    # # # # # # # # #
    # MY FUNCTIONS  #
    # # # # # # # # #

    def appendItem(self, item):
        assert isinstance(item, LeakItem)
        parent = QModelIndex()
        row_count = self.rowCount(parent)
        self.beginInsertRows(parent, row_count, row_count + 1)
        self.items.append(item)
        self.endInsertRows()

    def clearList(self):
        parent = QModelIndex()
        row_count = self.rowCount(parent)
        self.beginRemoveRows(QModelIndex(), 0, row_count - 1)
        self.items.clear()
        self.endRemoveRows()

    def updateFlag(self, index, flag_id):
        self.items[index.row()].high_prio_flag = flag_id
        self.dataChanged.emit(index, index, [Qt.DecorationRole])
