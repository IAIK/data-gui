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

from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QSizePolicy, QGroupBox, QGridLayout, QHBoxLayout, QButtonGroup, QTextEdit, QLabel
from PyQt5.QtGui import QColor, QFont, QFontMetrics
from datastub.leaks import Leak, NSLeak, NSPType, SPLeak
from datagui.package.utils import getCircle, getColor, createIconButton, LeakMetaInfo, LeakFlags, debug

btn_to_flag = {
    0: LeakFlags.NOLEAK,
    1: LeakFlags.INVESTIGATE,
    2: LeakFlags.LEAK,
    3: LeakFlags.DONTCARE
}

flag_to_btn = {
    LeakFlags.NOLEAK: 0,
    LeakFlags.INVESTIGATE: 1,
    LeakFlags.LEAK: 2,
    LeakFlags.DONTCARE: 3
}

import pdb

class SummaryTab(QWidget):
    def __init__(self, leak, updateFlagIcon, notifyUnsavedChanges):
        super(SummaryTab, self).__init__()
        assert isinstance(leak, Leak)
        assert isinstance(leak.meta, LeakMetaInfo)
        self.leak = leak
        self.user_comment = QTextEdit("")
        self.leak_details = QLabel(str(self.leak.status))
        self.updateFlagIcon = updateFlagIcon
        self.notifyUnsavedChanges = notifyUnsavedChanges
        self.setupUI()

    def setupUI(self):

        summary_layout = QGridLayout()
        self.user_comment.textChanged.connect(self.commentChanged)
        comment = self.leak.meta.comment
        if comment == "":
            self.user_comment.setPlaceholderText("User comments")
        else:
            self.user_comment.setText(comment)

        # # # # #
        flags_group_box = QGroupBox("Rating")
        #icon_size = QSize(20, 20)
        font_size = QFontMetrics(self.user_comment.currentFont()).size(0,"A").height()
        font_size *= 1
        icon_size = QSize(font_size, font_size)
        
        flag_0 = createIconButton(icon_size, LeakFlags.NOLEAK)
        flag_1 = createIconButton(icon_size, LeakFlags.INVESTIGATE)
        flag_2 = createIconButton(icon_size, LeakFlags.LEAK)
        flag_3 = createIconButton(icon_size, LeakFlags.DONTCARE)

        flag_0.setCheckable(True)
        flag_1.setCheckable(True)
        flag_2.setCheckable(True)
        flag_3.setCheckable(True)
        self.flags_button_group = QButtonGroup()
        self.flags_button_group.buttonClicked[int].connect(self.bgClicked)
        self.flags_button_group.setExclusive(True)
        self.flags_button_group.addButton(flag_0, 0)
        self.flags_button_group.addButton(flag_1, 1)
        self.flags_button_group.addButton(flag_2, 2)
        self.flags_button_group.addButton(flag_3, 3)

        btn_id = flag_to_btn[self.leak.meta.flag]
        self.flags_button_group.button(btn_id).setChecked(True)
        # # # # #
        flags_hbox = QHBoxLayout()
        flags_hbox.addWidget(flag_0)
        flags_hbox.addWidget(flag_1)
        flags_hbox.addWidget(flag_2)
        flags_hbox.addWidget(flag_3)
        flags_group_box.setLayout(flags_hbox)
        flags_group_box.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        #
        statistic_group_box = QGroupBox("Statistics")
        statistic_grid = QGridLayout()

        rowid = 0
        if self.leak.status is not None:
            if self.leak.status.nsperformed:
                # Only show the highest value for generic leaks
                l = max(self.leak.status.nsleak, key=lambda l: l.normalized())
                lbl_circle = QLabel()
                lbl_circle.setPixmap(getCircle(getColor(l.normalized(), l.threshold())))
                lbl_circle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                lbl_text = QLabel("%s: %0.1f%%" % ("generic", l.normalized() * 100.0))
                statistic_grid.addWidget(lbl_circle, rowid, 0)
                statistic_grid.addWidget(lbl_text, rowid, 1)
                rowid += 1
            if len(self.leak.status.spperformed) > 0:
                # Filter leaks: only keep the highest value
                spleaks = dict()
                for l in self.leak.status.spleak:
                    key = (l.target, l.property)
                    if key in spleaks and spleaks[key].normalized() >= l.normalized():
                        continue
                    spleaks[key] = l

                for key, l in sorted(spleaks.items()):
                    lbl_circle = QLabel()
                    lbl_circle.setPixmap(getCircle(getColor(l.normalized(), l.threshold())))
                    lbl_circle.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                    lbl_text = QLabel("%s[%s]: %0.1f%%" % (l.target, l.property, l.normalized() * 100.0))
                    statistic_grid.addWidget(lbl_circle, rowid, 0)
                    statistic_grid.addWidget(lbl_text, rowid, 1)
                    rowid += 1
        statistic_group_box.setLayout(statistic_grid)
        statistic_group_box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.leak_details.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        summary_layout.addWidget(flags_group_box, 0, 0)
        if rowid > 0:
            summary_layout.addWidget(statistic_group_box, 1, 0)
        summary_layout.addWidget(self.leak_details, 2, 0)
        summary_layout.addWidget(self.user_comment, 0, 1, 3, 1)

        self.setLayout(summary_layout)

    def bgClicked(self, btn_id):
        debug(5, "[bgClicked] flag_%d clicked", btn_id)
        flag_id = btn_to_flag[btn_id]
        self.leak.meta.flag = flag_id
        self.updateFlagIcon(self.leak.ip, flag_id)
        self.notifyUnsavedChanges()

    def commentChanged(self):
        comment = self.user_comment.toPlainText()
        debug(5, "[usrComment]: %s", comment)
        self.leak.meta.comment = comment
        self.notifyUnsavedChanges()
