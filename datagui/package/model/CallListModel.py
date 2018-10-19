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

    def __init__(self):
        super(CallListModel, self).__init__()
        self.root_item = None
        self.selected_leak = None

    # # # # # # # # # # # # #
    # OVERLOADED FUNCTIONS  #
    # # # # # # # # # # # # #
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return self.root_item.name

        return None

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            item = index.internalPointer()
            return item.description
        elif role == CustomRole.Obj:
            item = index.internalPointer()
            return item.data(CustomRole.Obj)
        elif role == CustomRole.Ip:
            item = index.internalPointer()
            return item.data(CustomRole.Ip)
        elif role == CustomRole.Id:
            item = index.internalPointer()
            return item.id
        elif role == CustomRole.CallItem:
            return index.internalPointer()
        elif role == Qt.DecorationRole:
            if index.column() == 0:
                flag_id = index.internalPointer().flag_id
                return utils.getIconById(flag_id)
            return QVariant()
        elif role == Qt.ToolTipRole:
            return index.internalPointer().description
        else:
            return QVariant()

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if parent.isValid():
            parent_item = parent.internalPointer()
        else:
            parent_item = self.root_item

        child_item = parent_item.child_items[row]
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return len(parent_item.child_items)

    def columnCount(self, parent):
        return 1

    # # # # # # # # #
    # MY FUNCTIONS  #
    # # # # # # # # #

    def setupDataWithExisting(self, selected_leak, item_leak_tuples, root_name):
        if item_leak_tuples is None:
            return None

        self.root_item = CallHierarchyItem(item_leak_tuples[0][0].name)
        self.selected_leak = selected_leak

        parent = QModelIndex()
        num_elements = len(item_leak_tuples)
        self.beginInsertRows(parent, 0, num_elements)

        for call_item, leak in item_leak_tuples:
            call_list_item = copy.copy(call_item)
            call_path = self.getCallPath(call_list_item, root_name)

            call_list_item.parent_item = self.root_item
            call_list_item.description = call_path
            call_list_item.flag_id = leak.meta.flag

            self.root_item.appendChild(call_list_item)

        self.endInsertRows()

    def getCallPath(self, call_item, root_name):
        rec_iterator = call_item

        function_names = []
        while rec_iterator.name != root_name:
            function_name = rec_iterator.name.split(" ")[-1].split("(")[0]
            function_names.insert(0, function_name)
            rec_iterator = rec_iterator.parent_item

        return '/'.join(function_names)
