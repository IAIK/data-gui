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

import copy

from PyQt5.QtCore import QModelIndex, QVariant, Qt

from datagui.package import utils
from datagui.package.model.BaseTreeModel import BaseTreeModel
from datagui.package.model.CallHierarchyModel import CallHierarchyItem
from datagui.package.utils import CustomRole


class CallListModel(BaseTreeModel):

    def __init__(self, selected_leak, item_leak_tuples, root_name):
        super(CallListModel, self).__init__()
        self.name = ""
        self.items = []
        self.none_item = CallHierarchyItem("No leaks visible.")
        self.selected_leak = None
        assert(item_leak_tuples is not None)
        if len(item_leak_tuples) == 0:
            return

        (item, leak) = item_leak_tuples[0]
        name = utils.leakToStr(selected_leak)
        self.name = name
        self.root_item = CallHierarchyItem(name)
        self.selected_leak = selected_leak

        parent = QModelIndex()
        num_elements = len(item_leak_tuples)
        self.beginInsertRows(parent, 0, num_elements)

        for call_item, leak in item_leak_tuples:
            call_list_item = copy.copy(call_item)
            call_path = self.getCallPath(call_list_item, root_name)
            assert call_list_item.parent_item is not None
            call_list_item.parent_item = self.root_item
            call_list_item.description = call_path
            call_list_item.flag_id = leak.meta.flag

            self.items.append(call_list_item)

        self.endInsertRows()

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

        if len(self.items) == 0:
            item = self.none_item
        else:
            item = self.items[index.row()]

        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            return item.description
        elif role == CustomRole.Obj:
            if len(self.items) == 0:
                return QVariant()
            else:
                return item.data(CustomRole.Obj)
        elif role == CustomRole.Ip:
            if len(self.items) == 0:
                return QVariant()
            else:
                return item.data(CustomRole.Ip)
        elif role == CustomRole.Id:
            return item.id
        elif role == CustomRole.CurrentItem:
            if len(self.items) == 0:
                return QVariant()
            else:
                return index.internalPointer()
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                return utils.getIconById(item.flag_id)
            return QVariant()
        else:
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

    def getCallPath(self, call_item, root_name):
        rec_iterator = call_item

        function_names = []
        while rec_iterator.parent_item:
            print(rec_iterator.name)
            function_name = rec_iterator.name.split(" ")[-1].split("(")[0]
            function_names.insert(0, function_name)
            rec_iterator = rec_iterator.parent_item
        return '/'.join(function_names)
