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

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget, QSizePolicy, QGroupBox, QGridLayout, QHBoxLayout, QButtonGroup, QTextEdit, QLabel
from datastub.leaks import Leak
from datagui.package.utils import getCircle, getColor, createIconButton, LeakMetaInfo, LeakFlags, debug

btn_to_flag = {
    0: LeakFlags.OKAY,
    1: LeakFlags.WARNING,
    2: LeakFlags.CANCEL,
    3: LeakFlags.GARBAGE
}

flag_to_btn = {
    LeakFlags.OKAY: 0,
    LeakFlags.WARNING: 1,
    LeakFlags.CANCEL: 2,
    LeakFlags.GARBAGE: 3
}

import pdb

class SummaryTab(QWidget):
    def __init__(self, leak, updateFlagIcon, notifyUnsavedChanges):
        super(SummaryTab, self).__init__()
        assert isinstance(leak, Leak)
        assert isinstance(leak.meta, LeakMetaInfo)
        self.leak = leak
        self.user_comment = QTextEdit("")
        self.leak_comment = QTextEdit("")
        self.updateFlagIcon = updateFlagIcon
        self.notifyUnsavedChanges = notifyUnsavedChanges
        self.setupUI()

    def setupUI(self):

        summary_layout = QGridLayout()
        lbl_c1 = QLabel()
        lbl_c1.setPixmap(getCircle(getColor(0, 0)))
        lbl_c2 = QLabel()
        lbl_c2.setPixmap(getCircle(getColor(1, 0)))
        lbl_c3 = QLabel()
        lbl_c3.setPixmap(getCircle(getColor(0, 1)))
        # # # # #
        lbl1 = QLabel("generic:\t10%")
        lbl2 = QLabel("specific:\t5%")
        lbl3 = QLabel("specific:\t3 %")
        #
        self.user_comment.textChanged.connect(self.commentChanged)
        comment = self.leak.meta.comment
        if comment == "":
            self.user_comment.setPlaceholderText("User comments")
        else:
            self.user_comment.setText(comment)
        self.leak_comment.setText(str(self.leak.status))

        # # # # #
        flags_group_box = QGroupBox("Risk Treatment")
        icon_size = QSize(20, 20)
        flag_0 = createIconButton(icon_size, LeakFlags.OKAY)
        flag_1 = createIconButton(icon_size, LeakFlags.WARNING)
        flag_2 = createIconButton(icon_size, LeakFlags.CANCEL)
        flag_3 = createIconButton(icon_size, LeakFlags.GARBAGE)

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
        #
        # percent_group_box = QGroupBox("Risk")
        # percent_grid = QGridLayout()
        # percent_grid.addWidget(lbl_c1, 0, 0)
        # percent_grid.addWidget(lbl1, 0, 1)
        # percent_grid.addWidget(lbl_c2, 1, 0)
        # percent_grid.addWidget(lbl2, 1, 1)
        # percent_grid.addWidget(lbl_c3, 2, 0)
        # percent_grid.addWidget(lbl3, 2, 1)
        # percent_group_box.setLayout(percent_grid)
        # percent_group_box.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        summary_layout.addWidget(flags_group_box, 0, 0)
        # summary_layout.addWidget(percent_group_box, 1, 0)
        #summary_layout.addWidget(self.user_comment, 0, 1, 2, 1)
        summary_layout.addWidget(self.leak_comment, 0, 1, 2, 1)

        lbl_c1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl_c2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lbl_c3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

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
