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

class ZoomTabView(QTabWidget):

    def __init__(self):
        super(ZoomTabView, self).__init__()
        self.zoomlevel = 0

    def scaleAllTabs(self, increment = 0):
        self.zoomlevel = int(self.zoomlevel + increment)
        for i in range(self.count() - 1):
            editor = self.widget(i)
            editor.SendScintilla(QsciScintilla.SCI_SETZOOM, self.zoomlevel)
            self.recomputeMarkers(editor)

    def wheelEvent(self, qwheelevent):
        numDegrees = qwheelevent.angleDelta() / 120
        self.scaleAllTabs(numDegrees.y())

