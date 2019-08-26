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
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics
from PyQt5.QtWidgets import QTabWidget, QFrame

from datagui.package.utils import LeakFlags, getIconById, debug, default_font_size


class SourceTabView(QTabWidget):

    def __init__(self):
        super(SourceTabView, self).__init__()
        self.empty_tab = QFrame()
        self.empty_tab_index = -1
        self.setStyleSheet("QTabWidget::pane { border: 1px solid blue; }")
        self.lexer_list = []
        self.zoomlevel = 0

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

        # - LineNumber - margin 0
        editor.setMarginType(0, QsciScintilla.NumberMargin)

        # - LeakMarker - margin 1
        editor.setMarginType(1, QsciScintilla.SymbolMargin)
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

        # MARGIN AND MARKERS
        # ------
        self.recomputeMarkers(editor)


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
        editor.setMarginWidth(0, "00000")
        editor.setMarginWidth(1, "000")

    def wheelEvent(self, qwheelevent):
        numDegrees = qwheelevent.angleDelta() / 120
        inc = numDegrees.y()
        self.zoomlevel = int(self.zoomlevel + inc)
        # Scales zoom level
        # fontsize remains constant
        for i in range(self.count() - 1):
            lexer = self.lexer_list[i]
            editor = lexer.editor()
            editor.SendScintilla(QsciScintilla.SCI_SETZOOM, self.zoomlevel)
            self.recomputeMarkers(editor)
