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

from PyQt5.Qsci import QsciScintilla, QsciLexerCPP
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QTabWidget, QFrame

from datagui.package.utils import LeakFlags, getIconById, debug, default_font_size


class SourceTabView(QTabWidget):

    def __init__(self):
        super(SourceTabView, self).__init__()
        self.empty_tab = QFrame()
        self.empty_tab_index = -1
        self.setStyleSheet("QTabWidget::pane { border: 1px solid blue; }")
        self.lexer_list = []

    def createNewSourceTab(self, source_file):

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
        editor.setCaretLineBackgroundColor(QColor("#1f0000ff"))

        # MARGIN
        # ------
        editor.setMarginsForegroundColor(QColor("#ff888888"))

        # DEFINE MARKERS
        # --------------
        icon_ok = getIconById(LeakFlags.OKAY)
        icon_warning = getIconById(LeakFlags.WARNING)
        icon_cancel = getIconById(LeakFlags.CANCEL)
        icon_default = getIconById(LeakFlags.GARBAGE)
        icon_arrow_right = getIconById(LeakFlags.RIGHT_ARROW)
        #
        sym_0 = icon_ok.pixmap(QSize(16, 16))
        sym_1 = icon_warning.pixmap(QSize(16, 16))
        sym_2 = icon_cancel.pixmap(QSize(16, 16))
        sym_3 = icon_default.pixmap(QSize(16, 16))
        sym_4 = icon_arrow_right.pixmap(QSize(16, 16))
        #
        editor.markerDefine(sym_0, LeakFlags.OKAY)
        editor.markerDefine(sym_1, LeakFlags.WARNING)
        editor.markerDefine(sym_2, LeakFlags.CANCEL)
        editor.markerDefine(sym_3, LeakFlags.GARBAGE)
        editor.markerDefine(sym_4, LeakFlags.RIGHT_ARROW)
        editor.setMarginMarkerMask(1, 0b11111)

        # - LineNumber - margin 0
        editor.setMarginType(0, QsciScintilla.NumberMargin)
        editor.setMarginWidth(0, "000000")

        # - LeakMarker - margin 1
        editor.setMarginType(1, QsciScintilla.SymbolMargin)
        editor.setMarginWidth(1, "000")
        editor.setMarginSensitivity(1, True)

        # SIGNALS
        # editor.marginClicked.connect(self.marginLeftClick)

        # INDICATORS
        editor.indicatorDefine(QsciScintilla.HiddenIndicator, 0)
        editor.setIndicatorHoverStyle(QsciScintilla.ThickCompositionIndicator, 0)
        editor.setIndicatorForegroundColor(QColor("#00f"), 0)
        editor.setIndicatorHoverForegroundColor(QColor("#00f"), 0)
        editor.setIndicatorDrawUnder(True, 0)

        # LEXER
        # -----
        lexer = QsciLexerCPP(editor)
        self.lexer_list.append(lexer)
        lexer.setFont(QFont("monospace", default_font_size, QFont.Normal), 0)
        editor.setLexer(lexer)
        self.setSourceCode(editor, source_file)

        tab_index = self.addTab(editor, source_file.name.split("/")[-1])
        return tab_index

    def setSourceCode(self, editor, source_file):
        try:
            editor.append(source_file.read())
        except FileNotFoundError:
            debug(1, "[NOT FOUND] %s", source_file.name)

    def jumpToLineNumber(self, tab_index, line_nr):
        editor = self.widget(tab_index)
        editor.setCursorPosition(line_nr, 0)

    def marginLeftClick(self, margin_nr, line_nr, state):
        debug(5, "[SRC] marginLeftClick\n\tmargin_nr: %d, line_nr: %d, state: %d", (margin_nr, line_nr, state))

    def changeFontsize(self, lexer_index, font_size):
        lexer = self.lexer_list[lexer_index]
        new_font = QFont("monospace", font_size, QFont.Normal)
        lexer.setFont(new_font)
