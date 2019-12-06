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

import copy

from PyQt5.QtCore import QModelIndex, QVariant, Qt
from PyQt5.QtGui import QStandardItem

from datagui.package import utils
from datagui.package.model.BaseTreeModel import BaseTreeModel
from datagui.package.model.CallHierarchyModel import CallHierarchyItem
from datagui.package.utils import CustomRole, CustomType, LeakFlags, getIconById


class CallListItem(QStandardItem):
    def __init__(self, name, call_item=None, leak=None, parent=None):
        super(CallListItem, self).__init__()
        self.name = name
        self.call_item = call_item
        self.leak = leak
        self.parent_item = parent

    def getDescription(self):
        return self.name

    def getFlag(self):
        return LeakFlags.INFO if self.leak is None else self.leak.meta.flag

    def type(self):
        return CustomType.callListItem

    def parent(self):
        return self.parent_item

class CallListModel(BaseTreeModel):

    def __init__(self):
        super(CallListModel, self).__init__()
        self.name = ""
        self.items = []
        self.root_item = None
        self.parent = None
        self.none_item = CallListItem("No leaks visible.")

    # # # # # # # # # # # # #
    # OVERLOADED FUNCTIONS  #
    # # # # # # # # # # # # #
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.name
        elif role == Qt.ToolTipRole:
            return "This leak occurs in different call contexts. Select one below."
        return None

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        item = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            return item.getDescription()
        elif role == CustomRole.Ip:
            return QVariant() if not item.leak else item.leak.ip
        elif role == CustomRole.Id:
            return item.id
        elif role == CustomRole.CurrentItem:
            return index.internalPointer()
        elif role == Qt.DecorationRole:
            if index.column() == 0:
              if item.leak:
                  return utils.getIconById(item.getFlag())
              else:
                  return utils.getIconById(LeakFlags.INFO)
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
        if parent.column() > 0:
            return 0
        if len(self.items) == 0:
            # We're empty. Display none_item
            return 1
        return len(self.items)

    def columnCount(self, parent):
        if parent.isValid():
            return 0
        else:
            return 1

    # # # # # # # # #
    # MY FUNCTIONS  #
    # # # # # # # # #

    def getCallPath(self, call_item):
        rec_iterator = call_item

        function_names = []
        assert call_item.parent_item is not None
        while rec_iterator.parent_item:
            function_name = rec_iterator.name.split(" ")[-1].split("(")[0]
            function_names.insert(0, function_name)
            rec_iterator = rec_iterator.parent_item
        return '/'.join(function_names)

    def appendItem(self, call_item, leak):
        # Generate long path-prefixed name
        assert isinstance(call_item, CallHierarchyItem)
        call_path = self.getCallPath(call_item)
        item = CallListItem(call_path, call_item, leak)

        # Add item to list
        parent = QModelIndex()
        row_count = self.rowCount(parent)
        self.beginInsertRows(parent, row_count, row_count + 1)
        self.items.append(item)
        self.endInsertRows()

        # Set header of CallList. Since every leak yields the same name
        # we can overwrite it for each new item
        self.name = utils.leakToStr(leak)
        self.root_item = CallListItem(self.name)
        self.parent = self.root_item

    def clearList(self):
        parent = QModelIndex()
        row_count = self.rowCount(parent)
        self.beginRemoveRows(QModelIndex(), 0, row_count - 1)
        self.items.clear()
        self.endRemoveRows()
