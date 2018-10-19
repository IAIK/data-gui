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

import sys
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QStandardItem, QPixmap, QColor, QPainter, QBrush, QIcon
from PyQt5.QtWidgets import QPushButton, QWidget, QStyle
from datastub.DataFS import DataFS
from datastub.SymbolInfo import SymbolInfo

datafs = None

info_map = {}  # info_map[ip] -> IpInfo
asm_map = {}  # asm_map[asm_tab_idx:line_nr] -> global ip
src_map = {}  # src_map[src_tab_idx:line_nr] -> global ip

leak_stack = []
stack_index = -1

debug_level = 0

default_font_size = 12


class StackInfo:
    """Class to store information to reset views to previously selected leak. """

    def __init__(self, coming_from_call_view, leak_ip, leak_idx):
        self.coming_from_call_view = coming_from_call_view
        self.leak_ip = leak_ip
        self.leak_idx = leak_idx # is only valid if coming_from_call_view is True

def appendStackInfo(stack_info):
    global stack_index
    if isinstance(stack_info, StackInfo):
        while stack_index < len(leak_stack) - 1:
            leak_stack.pop()

        leak_stack.append(stack_info)
        stack_index += 1
    else:
        debug(5, "[pushStackInfo] Wrong instance!")


def getPrevStackInfo():
    global stack_index
    if stack_index > 0:
        stack_index -= 1
        return leak_stack[stack_index]
    else:
        debug(5, "[getPrevStackInfo] Empty leak_stack: return None")
        return None


def getNextStackInfo():
    global stack_index
    if stack_index < len(leak_stack) - 1:
        stack_index += 1
        return leak_stack[stack_index]
    else:
        debug(5, "[getNextStackInfo] stack_index to high: return None")
        return None


def debuglevel(level):
    global debug_level
    return debug_level >= level


def set_debuglevel(level):
    global debug_level
    if level >= 0:
        debug_level = level


def debug(level, fstr, values=()):
    global debug_level
    if debug_level >= level:
        print(fstr % values)
        sys.stdout.flush()


class ErrorCode:
    INVALID_PICKLE = -1
    CANNOT_LOAD_PICKLE = -2
    INVALID_ZIP = -3
    CANNOT_LOAD_ZIP = -4
    INVALID_COMB_OF_FILES = -5

def createKey(tab_index, line_nr):
    """Return dictionary key: 'tab_index:line_nr'"""

    return "{}:{}".format(tab_index, line_nr)


class CustomRole:
    Obj = Qt.UserRole + 0
    Leak = Qt.UserRole + 1
    Info = Qt.UserRole + 2
    Ip = Qt.UserRole + 3
    Fentry = Qt.UserRole + 4
    Id = Qt.UserRole + 5
    CallItem = Qt.UserRole + 6


class CustomType:
    callHierarchyItem = QStandardItem.UserType + 0
    libHierarchyItem = QStandardItem.UserType + 1
    leakItem = QStandardItem.UserType + 2
    infoItem = QStandardItem.UserType + 3


class IpInfo:
    """Class to store information about global instruction pointers (ip)."""

    def __init__(self, asm_tab_index, asm_line_nr, asm_marker_handle, src_tab_index, src_line_nr, src_marker_handle,
                 lib_tree_item):
        self.asm_tab_index = asm_tab_index
        self.asm_line_nr = asm_line_nr
        self.asm_marker_handle = asm_marker_handle
        self.src_tab_index = src_tab_index
        self.src_line_nr = src_line_nr
        self.src_marker_handle = src_marker_handle
        self.lib_tree_item = lib_tree_item
        self.call_tree_items = []
        self.meta = LeakMetaInfo()

    def __str__(self):
        strings = ["IpInfo:",
                   "\tasm_tab_index:\t\t{}".format(self.asm_tab_index),
                   "\tasm_line_nr:\t\t{}".format(self.asm_line_nr),
                   "\tasm_marker_handle:\t{}".format(self.asm_marker_handle),
                   "\tsrc_tab_index:\t\t{}".format(self.src_tab_index),
                   "\tsrc_line_nr:\t\t{}".format(self.src_line_nr),
                   "\tsrc_marker_handle:\t{}".format(self.src_marker_handle),
                   "\tlib_tree_item:\t\t{}".format(self.lib_tree_item),
                   "\tcall_tree_items:\t{}".format(self.call_tree_items),
                   "\tmeta:\t{}".format(self.meta)]

        return "\n".join(strings)


def setupSymbolInfo(file_path):
    global datafs
    datafs = DataFS(file_path, write=False)
    with datafs.get_file("allsyms.txt") as f:
        SymbolInfo.open(f)


def resetSymbolInfo():
    SymbolInfo.close()


def getLocalIp(ip):
    """Find local ip using SymbolInfo."""

    if SymbolInfo.isopen():
        sym = SymbolInfo.lookup(ip)  # Type: SymbolInfo

        if sym is not None:
            if sym.img.dynamic:
                return ip - sym.img.lower
    return ip


def getCtxName(ip):
    """Find context name of ip.

    Returns:
        A string containing the context name, or the hex presentation
        of the ip of no SymbolInfo is available.
    """
    if SymbolInfo.isopen():
        sym = SymbolInfo.lookup(ip)  # Type: SymbolInfo

        if sym is not None:
            name = ""
            if sym.img is not None and sym.img.dynamic:
                name += "(+%x)" % (ip - sym.img.lower)

            name += " %s(%s)" % (sym.getname(), sym.type)
            return name
        else:
            return hex(ip)
    else:
        return hex(ip)


class LeakFlags:
    MISSING = -1
    GARBAGE = 0
    OKAY = 1
    WARNING = 2
    CANCEL = 3
    RIGHT_ARROW = 4
    LEFT_ARROW = 5


class LeakMetaInfo:
    def __init__(self):
        self.flag = LeakFlags.WARNING
        self.comment = ""

    def __str__(self):
        string = "Flag: " + str(self.flag) + ", "
        string += "Comment: "
        if self.comment == "":
            string += "[empty]"
        else:
            string += self.comment

        return string


def getIconById(flag_id):
    """Create a QIcon for a given flag id.

    Returns:
        A QIcon if the given flag_id is valid, None otherwise.
    """

    if flag_id == LeakFlags.OKAY:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_DialogApplyButton")))
    elif flag_id == LeakFlags.WARNING:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_MessageBoxWarning")))
    elif flag_id == LeakFlags.CANCEL:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_DialogCancelButton")))
    elif flag_id == LeakFlags.GARBAGE:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_TrashIcon")))
    elif flag_id == LeakFlags.RIGHT_ARROW:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_ArrowRight")))
    elif flag_id == LeakFlags.LEFT_ARROW:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_ArrowLeft")))
    elif flag_id == LeakFlags.MISSING:
        return QIcon(QWidget().style().standardIcon(getattr(QStyle, "SP_MessageBoxQuestion")))
    else:
        debug(1, "[getIconById] UNKNOWN flag id: %d", flag_id)
        return None


class ColorScheme:
    CALL = "CALL"
    LIB = "LIB"
    BOTH = "BOTH"


def getCircle(color):
    """Create a QPixmap object which displays a colored circle."""

    pixmap = QPixmap(15, 15)
    pixmap.fill(QColor("transparent"))

    painter = QPainter(pixmap)
    QColor(0, 0, 255, 255)
    painter.setBrush(QBrush(color))
    painter.drawEllipse(0, 0, 10, 10)
    painter.end()

    return pixmap


def getColor(value, treshold):
    # value    in [0,1]
    # treshold in [0,1]
    # HSL = (hue, saturation, lightning)

    hue = 120 * (1 - value)
    saturation = 255 * (1 - treshold)
    # saturation = 255
    lightness = 100
    # alpha = 255 * (1 - treshold)
    color = QColor()
    color.setHsl(hue, saturation, lightness, 255)
    return color


def createIconButton(size, icon_id):
    """Create a icon button which is a QPushButton object."""

    btn = QPushButton()
    btn.setIcon(getIconById(icon_id))
    btn.setIconSize(size)
    btn.setFixedSize(QSize(size.width() + 5, size.height() + 5))

    return btn
