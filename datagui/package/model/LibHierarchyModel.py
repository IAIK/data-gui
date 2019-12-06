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

from PyQt5.QtCore import QModelIndex, QVariant, Qt
from datastub.leaks import FunctionLeak

from datagui.package.model.BaseTreeItem import BaseTreeItem
from datagui.package.model.BaseTreeModel import BaseTreeModel
from datagui.package.utils import CustomType, CustomRole


class LibHierarchyItem(BaseTreeItem):
    id = -1

    def __init__(self, name, obj=None, parent=None):
        super(LibHierarchyItem, self).__init__(name, obj, parent)
        self.id = LibHierarchyItem.id = LibHierarchyItem.id + 1

    def type(self):
        return CustomType.LibHierarchyItem


class LibHierarchyModel(BaseTreeModel):

    def __init__(self, lib_hierarchy=None):
        super(LibHierarchyModel, self).__init__()
        self.root_item = None
        if lib_hierarchy is not None:
            self.setRootItem(lib_hierarchy)

    def setRootItem(self, lib_hierarchy):
        if lib_hierarchy is not None:
            self.root_item = LibHierarchyItem("Library Hierarchy", lib_hierarchy)

    # # # # # # # # # # # # #
    # OVERLOADED FUNCTIONS  #
    # # # # # # # # # # # # #

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            item = index.internalPointer()
            return item.data(Qt.DisplayRole)
        elif role == CustomRole.Obj:
            item = index.internalPointer()
            return item.data(CustomRole.Obj)
        elif role == CustomRole.CurrentItem:
            return index.internalPointer()
        elif role == CustomRole.Id:
            item = index.internalPointer()
            return item.id
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

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return ["Library Hierarchy"][section]
        elif role == Qt.ToolTipRole:
            return ["Leaks sorted and collected per library and function"][section]
        return None
