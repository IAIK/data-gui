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

from PyQt5.Qsci import QsciScintilla
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics
from PyQt5.QtWidgets import QTabWidget, QFrame

from datagui.package.utils import getIconById, LeakFlags, debug, default_font_size


class AsmTabView(QTabWidget):

    def __init__(self):
        super(AsmTabView, self).__init__()
        self.empty_tab = QFrame()
        self.empty_tab_index = -1
        self.setStyleSheet("QTabWidget::pane { border: 1px solid red;}")

    def createNewAsmTab(self, file_path, asm_dump):
        editor = QsciScintilla()
        # TABS & READ ONLY
        # ------------------
        editor.setIndentationsUseTabs(False)
        editor.setTabWidth(2)
        editor.setReadOnly(True)

        # CARET
        # -----
        editor.setCaretLineVisible(True)
        editor.setCaretWidth(2)
        editor.setCaretLineBackgroundColor(QColor("#1fff0000"))

        # MARGIN
        # ------
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        # - LeakMarker - margin 1
        editor.setMarginType(1, QsciScintilla.SymbolMargin)
        editor.setMarginSensitivity(1, True)

        # SIGNALS
        # editor.marginClicked.connect(self.marginLeftClick)

        # INDICATORS
        editor.indicatorDefine(QsciScintilla.TextColorIndicator, 0)
        editor.setIndicatorHoverStyle(QsciScintilla.ThickCompositionIndicator, 0)
        editor.setIndicatorForegroundColor(QColor("#f00"), 0)
        editor.setIndicatorHoverForegroundColor(QColor("#f00"), 0)
        editor.setIndicatorDrawUnder(True, 0)

        # FONT
        # ----
        editor.setFont(QFont("monospace", default_font_size, QFont.Normal))

        # EDITOR CONTENT
        # --------------
        editor.append(asm_dump)

        # MARGIN AND MARKERS
        # ------
        self.setMargin(editor, editor.textHeight(0))

        tab_index = self.addTab(editor, file_path.split("/")[-1])
        return tab_index

    def jumpToLine(self, tab_index, line_nr):
        editor = self.widget(tab_index)
        editor.setCursorPosition(line_nr, 0)
        editor.setFocus()

    def marginLeftClick(self, margin_nr, line_nr, state):
        debug(5, "[ASM] marginLeftClick\n\tmargin_nr: %d, line_nr: %d, state: %d", (margin_nr, line_nr, state))

    def changeFontsize(self, tab_index, font_size):
        if tab_index == -1:
            for i in range(self.count() - 1):
                self.changeFontsize(i, font_size)
            return

        editor = self.widget(tab_index)
        if font_size >= 0:
            new_font = QFont("monospace", font_size, QFont.Normal)
            editor.setFont(new_font)

        icon_size = editor.textHeight(0)
        self.setMargin(editor, icon_size)

    def setMargin(self, editor, height):
        size = QSize(height,height)
        #
        icon_ok = getIconById(LeakFlags.NOLEAK)
        icon_warning = getIconById(LeakFlags.INVESTIGATE)
        icon_cancel = getIconById(LeakFlags.LEAK)
        icon_default = getIconById(LeakFlags.DONTCARE)
        icon_arrow_right = getIconById(LeakFlags.RIGHT_ARROW)
        #
        sym_0 = icon_ok.pixmap(size)
        sym_1 = icon_warning.pixmap(size)
        sym_2 = icon_cancel.pixmap(size)
        sym_3 = icon_default.pixmap(size)
        sym_4 = icon_arrow_right.pixmap(size)
        #
        editor.markerDefine(sym_0, LeakFlags.NOLEAK)
        editor.markerDefine(sym_1, LeakFlags.INVESTIGATE)
        editor.markerDefine(sym_2, LeakFlags.LEAK)
        editor.markerDefine(sym_3, LeakFlags.DONTCARE)
        editor.markerDefine(sym_4, LeakFlags.RIGHT_ARROW)
        editor.setMarginMarkerMask(1, 0b11111)

        # set margin width (based on updated font size)
        editor.setMarginWidth(1, "000")

    def wheelEvent(self, qwheelevent):
        if qwheelevent.modifiers() == Qt.ControlModifier:
            self.changeFontsize(-1, -1)
            pass
