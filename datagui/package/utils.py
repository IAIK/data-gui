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
import os
import traceback
import datetime
from pkg_resources import resource_filename
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QStandardItem, QPixmap, QColor, QPainter, QBrush, QIcon, QFontDatabase, QFont, QFontMetrics
from PyQt5.QtWidgets import QPushButton, QWidget, QStyle, QLabel
from datastub.DataFS import DataFS
from datastub.SymbolInfo import SymbolInfo
from datastub.export import MyUnpickler
from datastub.leaks import DataLeak, CFLeak, Leak

datafs = None

info_map = {}  # info_map[ip] -> IpInfo
asm_map = {}  # asm_map[asm_tab_idx:line_nr] -> global ip
src_map = {}  # src_map[src_tab_idx:line_nr] -> global ip

leak_stack = []
stack_index = -1

debug_level = 4

default_font_size = 12

def loadipinfo(pfile):
    unp = MyUnpickler(pfile, encoding='latin1')
    return unp.load()

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


def getCurrentStackInfo():
    global stack_index
    if stack_index >= 0:
        return leak_stack[stack_index]
    else:
        debug(1, "[getCurrentStackInfo] Empty leak_stack: return None")
        return None

def getPrevStackInfo():
    global stack_index
    if stack_index > 0:
        stack_index -= 1
        return leak_stack[stack_index]
    else:
        debug(1, "[getPrevStackInfo] Empty leak_stack: return None")
        return None

def getNextStackInfo():
    global stack_index
    if stack_index < len(leak_stack) - 1:
        stack_index += 1
        return leak_stack[stack_index]
    else:
        debug(1, "[getNextStackInfo] stack_index to high: return None")
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
    ASSERT = -6

def createKey(tab_index, line_nr):
    """Return dictionary key: 'tab_index:line_nr'"""

    return "{}:{}".format(tab_index, line_nr)


class CustomRole:
    Obj = Qt.UserRole + 0
    Leak = Qt.UserRole + 1
    Info = Qt.UserRole + 2
    Ip = Qt.UserRole + 3
    Id = Qt.UserRole + 4
    CurrentItem = Qt.UserRole + 5


class CustomType:
    callHierarchyItem = QStandardItem.UserType + 0
    LibHierarchyItem = QStandardItem.UserType + 1
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

def leakToStr(leak):
    if isinstance(leak, DataLeak):
        leak_type = "DataLeak"
    elif isinstance(leak, CFLeak):
        leak_type = "CFLeak"
    else:
        leak_type = "UnknownLeak"
    leak_detail_short = ""
    is_leak = leak.status.is_generic_leak() or leak.status.is_specific_leak()
    if is_leak:
        normalized = leak.status.max_leak_normalized()
        if normalized >= 0.005:
            leak_detail_short = " (%0.1f%%)" % (normalized * 100)
    return "{}: {}{}".format(
        leak_type,
        hex(getLocalIp(leak.ip)),
        leak_detail_short)

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
    DONTCARE = 0
    NOLEAK = 1
    INVESTIGATE = 2
    LEAK = 3
    RIGHT_ARROW = 4
    LEFT_ARROW = 5

class LeakMetaInfo:
    def __init__(self):
        self.flag = LeakFlags.INVESTIGATE
        self.comment = ""

    def __str__(self):
        string = "Flag: " + str(self.flag) + ", "
        string += "Comment: "
        if self.comment == "":
            string += "[empty]"
        else:
            string += self.comment

        return string

def getResourcePath(*args):
    path = os.path.join(os.path.sep, '..', 'resources', *args)
    return resource_filename(__package__, path)

def getIconUnicodeById(flag_id):
    icons = {
        LeakFlags.NOLEAK:      u'\uf058', # check-circle
        LeakFlags.INVESTIGATE: u'\uf059', # question-circle
        LeakFlags.LEAK:        u'\uf043', # tint
        LeakFlags.DONTCARE:    u'\uf1f8', # trash
        LeakFlags.RIGHT_ARROW: u'\uf105', # angle-right
        LeakFlags.LEFT_ARROW:  u'\uf104', # angle-left
        LeakFlags.MISSING:     u'\uf129', # info
    }
    if flag_id not in icons:
        flag_id = LeakFlags.MISSING
    return icons[flag_id]

def getIconColorById(flag_id):
    colors = {
        LeakFlags.NOLEAK:      0x2ecc71,
        LeakFlags.INVESTIGATE: 0xf1c40f, 
        LeakFlags.LEAK:        0xe74c3c,
        LeakFlags.DONTCARE:    0x666666,
        LeakFlags.RIGHT_ARROW: 0x333333,
        LeakFlags.LEFT_ARROW:  0x333333,
        LeakFlags.MISSING:     0x3498db,
    }
    if flag_id not in colors:
        flag_id = LeakFlags.MISSING
    return colors[flag_id]

def getIconById(flag_id, height = None):
    if not height:
        height = getDefaultIconSize().height()
    unscaled_size = getDefaultIconSize()
    pix = QPixmap(QSize(height, height))
    pix.fill(QColor("transparent"))
    painter = QPainter(pix)
    painter.setFont(QFont("Font Awesome 5 Free Solid", default_font_size))
    painter.setPen(QColor.fromRgb(getIconColorById(flag_id)))
    scale = height / unscaled_size.height()
    # Scaling transforms the coordinate system for subsequent draw events
    painter.scale(scale, scale)
    painter.drawText(QRect(0, 0, unscaled_size.width(), unscaled_size.height()), Qt.AlignCenter, getIconUnicodeById(flag_id))
    painter.end()
    return pix

def getLogoIcon():
    icon = QIcon()
    icon.addFile(getResourcePath('icons', 'window_icon.png'))
    return icon

def getLogoIconPixmap():
    icon = QPixmap()
    icon.load(getResourcePath('icons', 'window_icon.png'))
    return icon

def getResourceFile(*filename):
    return open(getResourcePath(*filename), 'r')

def getIconTooltipById(flag_id):
    """Return a tooltip for a given flag id.

    Returns:
        A QIcon if the given flag_id is valid, None otherwise.
    """

    if flag_id == LeakFlags.NOLEAK:
        return "No leak"
    elif flag_id == LeakFlags.INVESTIGATE:
        return "Investigate"
    elif flag_id == LeakFlags.LEAK:
        return "Leak"
    elif flag_id == LeakFlags.DONTCARE:
        return "Do not care"
    elif flag_id == LeakFlags.RIGHT_ARROW:
        return "Go to next leak"
    elif flag_id == LeakFlags.LEFT_ARROW:
        return "Go to previous leak"
    elif flag_id == LeakFlags.MISSING:
        return None
    else:
        debug(1, "[getIconTooltipById] UNKNOWN flag id: %d", flag_id)
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

def getColor(value, threshold):
    # value    in [0,1]
    # threshold in [0,1]
    # HSL = (hue, saturation, lightning)

    hue = 120 * (1 - value)
    saturation = 255 * (1 - threshold)
    # saturation = 255
    lightness = 100
    # alpha = 255 * (1 - threshold)
    color = QColor()
    color.setHsl(hue, saturation, lightness, 255)
    return color

def createIconButton(size, flag_id):
    """Create a icon button which is a QPushButton object."""
    btn = QPushButton()
    btn.setFont(QFont("Font Awesome 5 Free Solid", default_font_size))
    btn.setText(getIconUnicodeById(flag_id))
    btn.setStyleSheet('QPushButton {color: #%06X;}' % getIconColorById(flag_id))
    btn.setToolTip(getIconTooltipById(flag_id))
    btn.setFixedSize(QSize(size.width() + 5, size.height() + 5))
    return btn

def global_exception_handler(tt, value, tb):
    fe = traceback.format_exception(tt, value, tb)
    msg = "".join(fe)
    debug(0, "ASSERT: %s", msg)
    try:
        with open('datagui.log', 'a') as f:
            f.write("####\\n")
            f.write(str(datetime.datetime.now()) + "\\n")
            f.write(msg)
    except:
        debug(0, "Error writing datagui.log!")
    if assert_handler:
        assert_handler(msg)

assert_handler = None

def register_assert_handler(handler):
    global assert_handler
    assert_handler = handler

sys.excepthook = global_exception_handler

def registerFonts():
    QFontDatabase.addApplicationFont(getResourcePath('Font Awesome 5 Free-Solid-900.otf'))

def getDefaultIconSize():
    icon_size = QFontMetrics(QFont()).size(0,"Ag").height()
    icon_size = QSize(icon_size, icon_size)
    return icon_size
