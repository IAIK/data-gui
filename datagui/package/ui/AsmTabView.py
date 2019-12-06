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

from PyQt5.Qsci import QsciScintilla
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics
from PyQt5.QtWidgets import QTabWidget, QFrame

from datagui.package.ui.ZoomTabView import ZoomTabView
from datagui.package.utils import getIconById, LeakFlags, debug, default_font_size


class AsmTabView(ZoomTabView):

    def __init__(self):
        super(AsmTabView, self).__init__()
        self.empty_tab = QFrame()
        self.empty_tab_index = -1
        self.setStyleSheet("QTabWidget::pane { border: 1px solid red;}")
        self.zoomlevel = 0

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
        self.recomputeMarkers(editor)

        tab_index = self.addTab(editor, file_path.split("/")[-1])
        return tab_index

    def jumpToLine(self, tab_index, line_nr):
        editor = self.widget(tab_index)
        editor.setCursorPosition(line_nr, 0)
        editor.setFocus()

    def marginLeftClick(self, margin_nr, line_nr, state):
        debug(5, "[ASM] marginLeftClick\n\tmargin_nr: %d, line_nr: %d, state: %d", (margin_nr, line_nr, state))

    def recomputeMarkers(self, editor):
        height = editor.textHeight(0)
        sym_0 = getIconById(LeakFlags.NOLEAK, height)
        sym_1 = getIconById(LeakFlags.INVESTIGATE, height)
        sym_2 = getIconById(LeakFlags.LEAK, height)
        sym_3 = getIconById(LeakFlags.DONTCARE, height)
        sym_4 = getIconById(LeakFlags.RIGHT_ARROW, height)

        editor.markerDefine(sym_0, LeakFlags.NOLEAK)
        editor.markerDefine(sym_1, LeakFlags.INVESTIGATE)
        editor.markerDefine(sym_2, LeakFlags.LEAK)
        editor.markerDefine(sym_3, LeakFlags.DONTCARE)
        editor.markerDefine(sym_4, LeakFlags.RIGHT_ARROW)
        editor.setMarginMarkerMask(1, 0b11111)

        # set margin width (based on updated font size)
        editor.setMarginWidth(1, "000")
