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

from PyQt5.QtCore import QAbstractItemModel, Qt, QModelIndex

class BaseTreeModel(QAbstractItemModel):
    def __init__(self):
        super(BaseTreeModel, self).__init__()

    # # # # # # # # # # # # #
    # OVERLOADED FUNCTIONS  #
    # # # # # # # # # # # # #

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root_item.name

        return None

    def parent(self, index):
        if not index.isValid() or index is None:
            return QModelIndex()

        child_item = index.internalPointer()

        # TODO: sometimes, child_item.parent() fails with
        # AttributeError: 'CallHierarchyItem' object has no attribute 'parent_item'
        # Although, that should not occur because CallHierarchyItem implements parent_item
        # via its superclass BaseTreeItem
        parent_item = child_item.parent()

        if parent_item == self.root_item or parent_item is None:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)
