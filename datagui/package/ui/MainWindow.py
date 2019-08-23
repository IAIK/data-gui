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
import datetime

from PyQt5.Qsci import QsciScintilla
from PyQt5.QtCore import Qt, QVariant, QModelIndex, QItemSelectionModel, QSize
from PyQt5.QtGui import QBrush, QColor, QIcon, QPalette
from PyQt5.QtWidgets import QMainWindow, QFrame, QSplitter, QHBoxLayout, QAction, QApplication, QTabWidget, \
    QTreeView, QMenu, QStackedWidget, QFileDialog, QStyle, QMessageBox, QHeaderView
from datastub.export import *
from datastub.DataFS import *
from datastub.IpInfoShort import *
from datastub.IpInfoShort import IP_INFO_FILE
from datastub.leaks import Library, FunctionLeak, DataLeak, CFLeak, CallHistory, LibHierarchy, Leak
from datastub.utils import sorted_keys

from datagui import DATAGUI_VERSION
from datagui.package import utils
from datagui.package.model.CallHierarchyModel import CallHierarchyModel, CallHierarchyItem
from datagui.package.model.CallListModel import CallListModel
from datagui.package.model.LeakModel import LeakModel, LeakItem
from datagui.package.model.LibHierarchyModel import libHierarchyModel, libHierarchyItem
from datagui.package.ui.AsmTabView import AsmTabView
from datagui.package.ui.SourceTabView import SourceTabView
from datagui.package.ui.SummaryTab import SummaryTab
from datagui.package.utils import ErrorCode, CustomRole, IpInfo, info_map, LeakMetaInfo, ColorScheme, LeakFlags, debug, \
    getCtxName, default_font_size, createIconButton, register_assert_handler, loadipinfo, leakToStr

mainWindow = None

def assert_handler(msg):
    dump_path = mainWindow.pickle_path
    if dump_path is None or dump_path == "":
        dump_path = "dump.pickle"
    dump_path += "." + str(datetime.datetime.now().time()) + ".autosave"
    storepickle(dump_path, mainWindow.call_hierarchy)
    debug(0, "Dumped pickle file to %s", (dump_path))
    if mainWindow:
        mainWindow.askAssert(msg, dump_path)

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.pickle_path = ""
        self.dialog_path = "."
        self.unsaved_changes = False
        self.call_hierarchy = None # Only for assert_handler
        #~ self.leakFilter = LeakFilter()

        global mainWindow
        mainWindow = self

        register_assert_handler(assert_handler)

        if len(sys.argv) == 3:
            self.pickle_path = sys.argv[1]
            self.dialog_path = os.path.dirname(os.path.abspath(self.pickle_path))
            try:
                self.call_hierarchy = loadpickle(self.pickle_path)
                if not self.call_hierarchy:
                    raise FileNotFoundError()
            except FileNotFoundError:
                debug(0, "Please enter a valid pickle file path (mandatory)")
                sys.exit(ErrorCode.INVALID_PICKLE)
            except Exception as e:
                debug(0, "Unable to load pickle file")
                debug(1, "Exception: " + str(e))
                sys.exit(ErrorCode.CANNOT_LOAD_PICKLE)

            try:
                utils.setupSymbolInfo(sys.argv[2])
            except FileNotFoundError:
                debug(0, "Please enter a valid zip file path (mandatory)")
                sys.exit(ErrorCode.INVALID_ZIP)
            except:
                debug(0, "Unable to load zip file")
                sys.exit(ErrorCode.CANNOT_LOAD_ZIP)
        else:
            self.call_hierarchy = self.openFiles()

        if self.call_hierarchy is None:
            debug(0, "Error opening pickle/zip file")
            sys.exit(ErrorCode.CANNOT_LOAD_PICKLE)

        lib_hierarchy = self.call_hierarchy.flatten()

        self.main_view = QFrame(self)
        self.asm_tab = AsmTabView()
        self.src_tab = SourceTabView()
        self.editor_font_size = default_font_size
        self.call_model = CallHierarchyModel()
        self.call_view = QTreeView()
        self.leak_model = LeakModel()
        self.leak_view = QTreeView()
        self.lib_model = libHierarchyModel()
        self.lib_view = QTreeView()
        self.info_view = QTabWidget()
        self.coming_from_call_view = False
        self.call_list_view = QTreeView()
        #self.call_list_model = CallListModel()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.info_view)
        self.stacked_widget.addWidget(self.call_list_view)
        self.stacked_widget.hide()
        # # # # #
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.code_splitter = QSplitter(Qt.Vertical)
        self.view_splitter = QSplitter(Qt.Horizontal)
        self.hierarchy_splitter = QSplitter(Qt.Vertical)
        self.info_splitter = QSplitter(Qt.Vertical)
        self.main_hbox = QHBoxLayout(self.main_view)
        self.main_toolbar = self.addToolBar('main')
        self.btn_back = utils.createIconButton(QSize(20, 20), LeakFlags.LEFT_ARROW)
        self.btn_forward = utils.createIconButton(QSize(20, 20), LeakFlags.RIGHT_ARROW)
        self.btn_filter_0 = utils.createIconButton(QSize(20, 20), LeakFlags.NOLEAK)
        self.btn_filter_1 = utils.createIconButton(QSize(20, 20), LeakFlags.INVESTIGATE)
        self.btn_filter_2 = utils.createIconButton(QSize(20, 20), LeakFlags.LEAK)
        self.btn_filter_3 = utils.createIconButton(QSize(20, 20), LeakFlags.DONTCARE)

        icon_size = QSize(20, 20)
        self.btn_filter_0 = createIconButton(icon_size, LeakFlags.NOLEAK)
        self.btn_filter_1 = createIconButton(icon_size, LeakFlags.INVESTIGATE)
        self.btn_filter_2 = createIconButton(icon_size, LeakFlags.LEAK)
        self.btn_filter_3 = createIconButton(icon_size, LeakFlags.DONTCARE)

        self.btn_filter_0.setCheckable(True)
        self.btn_filter_1.setCheckable(True)
        self.btn_filter_2.setCheckable(True)
        self.btn_filter_3.setCheckable(True)
        self.btn_filter_0.setChecked(True)
        self.btn_filter_1.setChecked(True)
        self.btn_filter_2.setChecked(True)
        self.btn_filter_3.setChecked(True)

        self.statusbar = self.statusBar()
        # # # # #
        self.setupMenu()
        self.setupUI()
        self.setupCallTree(self.call_hierarchy)
        self.setupLibTree(lib_hierarchy)
        self.setupLeakTree()
        self.setupInfoMap(lib_hierarchy)
        self.setupEmptyTabs()
        self.setupHistoryButtons()
        self.setupConnections()
        self.call_view.expandAll()
        self.lib_view.expandAll()
        self.setupWindowInfo()
        #

    def setupMenu(self):
        # # # # # #
        # ACTIONS #
        # # # # # #
        exit_act = QAction(QIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogCloseButton"))), '&Exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit the Application')
        exit_act.triggered.connect(self.closeGUI)
        #
        toggle_call_act = QAction('&Call Hierarchy', self, checkable=True)
        toggle_call_act.triggered.connect(self.toggleCall)  # lambda: self.on_button(1)
        toggle_call_act.setChecked(True)
        toggle_call_act.setShortcut('F1')
        #
        toggle_lib_act = QAction('&Lib Hierarchy', self, checkable=True)
        toggle_lib_act.triggered.connect(self.toggleLib)
        toggle_lib_act.setChecked(True)
        toggle_lib_act.setShortcut('F2')
        #
        toggle_leak_act = QAction('&Leak View', self, checkable=True)
        toggle_leak_act.triggered.connect(self.toggleLeak)
        toggle_leak_act.setChecked(True)
        toggle_leak_act.setShortcut('F3')
        #
        toggle_info_act = QAction('&Info View', self, checkable=True)
        toggle_info_act.triggered.connect(self.toggleStacked)
        toggle_info_act.setChecked(False)
        toggle_info_act.setShortcut('F4')
        #
        toggle_asm_act = QAction('&ASM Editor', self, checkable=True)
        toggle_asm_act.triggered.connect(self.toggleASM)
        toggle_asm_act.setChecked(True)
        toggle_asm_act.setShortcut('F5')
        #
        toggle_source_act = QAction('&Source Editor', self, checkable=True)
        toggle_source_act.triggered.connect(self.toggleSource)
        toggle_source_act.setChecked(True)
        toggle_source_act.setShortcut('F6')
        #
        open_file_act = QAction(QIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogOpenButton"))), '&Open', self)
        open_file_act.setShortcut('Ctrl+O')
        open_file_act.setStatusTip('Open existing files')
        open_file_act.triggered.connect(self.reopenFiles)
        #
        save_file_act = QAction(QIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogSaveButton"))),
                                '&Save pickle', self)
        save_file_act.setShortcut('Ctrl+S')
        save_file_act.setStatusTip('Save current file')
        save_file_act.triggered.connect(self.saveExistingCallHierarchy)
        #
        save_as_file_act = QAction(QIcon(self.style().standardIcon(getattr(QStyle, "SP_DialogSaveButton"))),
                                   'Save pickle &As ...', self)
        save_as_file_act.setStatusTip('Save current file as ...')
        save_as_file_act.triggered.connect(self.saveCallHierarchy)
        #
        font_inc_act = QAction('&Increase size', self)
        font_inc_act.triggered.connect(self.increaseFontSize)
        font_inc_act.setShortcut('Ctrl++')
        #
        font_dec_act = QAction('&Decrease size', self)
        font_dec_act.triggered.connect(self.decreaseFontSize)
        font_dec_act.setShortcut('Ctrl+-')
        # # # # # #
        # MENUBAR #
        # # # # # #
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(open_file_act)
        file_menu.addAction(save_file_act)
        file_menu.addAction(save_as_file_act)
        file_menu.addAction(exit_act)

        self.view_menu = menu_bar.addMenu('&View')
        self.view_menu.addAction(toggle_call_act)
        self.view_menu.addAction(toggle_lib_act)
        self.view_menu.addAction(toggle_leak_act)
        self.view_menu.addAction(toggle_info_act)
        self.view_menu.addAction(toggle_asm_act)
        self.view_menu.addAction(toggle_source_act)

        # Uncomment to activate Editor font manipulations
        editor_menu = menu_bar.addMenu('&Editor')
        editor_menu.addAction(font_inc_act)
        editor_menu.addAction(font_dec_act)
        # # # # # #
        # TOOLBAR #
        # # # # # #
        self.main_toolbar.addWidget(self.btn_back)
        self.main_toolbar.addWidget(self.btn_forward)
        self.main_toolbar.addWidget(self.btn_filter_0)
        self.main_toolbar.addWidget(self.btn_filter_1)
        self.main_toolbar.addWidget(self.btn_filter_2)
        self.main_toolbar.addWidget(self.btn_filter_3)
        # # # # # # #
        # STATUSBAR #
        # # # # # # #
        self.statusbar.showMessage('Ready')

    def closeEvent(self, evnt):
        debug(1, "About to close")
        if not self.askUnsavedChanges():
            evnt.ignore()

    def setupUI(self):
        """Setup main layout for the user interface"""
        # # # # #
        self.hierarchy_splitter.addWidget(self.call_view)
        self.hierarchy_splitter.addWidget(self.lib_view)
        # # # # #
        self.view_splitter.addWidget(self.hierarchy_splitter)
        self.view_splitter.addWidget(self.leak_view)
        self.view_splitter.setStretchFactor(0, 2)
        self.view_splitter.setStretchFactor(1, 1)
        # # # # #
        self.info_splitter.addWidget(self.view_splitter)
        self.info_splitter.addWidget(self.stacked_widget)
        self.info_splitter.setStretchFactor(0, 2)
        self.info_splitter.setStretchFactor(1, 1)
        self.info_splitter.setContentsMargins(0, 0, 10, 0)
        # # # # #
        self.code_splitter.addWidget(self.asm_tab)
        self.code_splitter.addWidget(self.src_tab)
        self.code_splitter.setStretchFactor(0, 1)
        self.code_splitter.setStretchFactor(1, 1)
        self.code_splitter.setContentsMargins(10, 0, 0, 0)
        # # # # #
        self.main_splitter.addWidget(self.info_splitter)
        self.main_splitter.addWidget(self.code_splitter)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 2)
        # # # # #
        self.main_hbox.addWidget(self.main_splitter)
        self.main_view.setLayout(self.main_hbox)
        self.setCentralWidget(self.main_view)

    def setupCallTree(self, call_hierarchy):
        self.call_model.setupData(call_hierarchy)
        self.call_view.setModel(self.call_model)
        self.call_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.call_view.setContextMenuPolicy(Qt.CustomContextMenu)

    def setupLibTree(self, lib_hierarchy):
        self.lib_model.setRootItem(lib_hierarchy)
        self.lib_view.setModel(self.lib_model)

    def setupLeakTree(self):
        self.leak_view.setModel(self.leak_model)

    def setupEmptyTabs(self):
        """Add empty tabs to asm and src editor.

        In case we have no information for a specific leak
        we can switch to an empty tab.
        """
        self.asm_tab.empty_tab_index = self.asm_tab.addTab(self.asm_tab.empty_tab, "No file")
        self.asm_tab.setTabToolTip(self.asm_tab.empty_tab_index, "Objdump not available")
        self.src_tab.empty_tab_index = self.src_tab.addTab(self.src_tab.empty_tab, "No file")
        self.src_tab.setTabToolTip(self.src_tab.empty_tab_index, "Source file not available")

    def setupHistoryButtons(self):
        utils.leak_stack.clear()
        utils.stack_index = -1
        self.btn_back.setEnabled(False)
        self.btn_forward.setEnabled(False)

    def setupConnections(self):
        """Setup all clicked connections.

        The function gets only called once, otherwise the click event would trigger multiple times.
        """

        self.call_list_view.clicked.connect(self.callListClicked)
        self.call_view.clicked.connect(self.callClicked)
        self.call_view.customContextMenuRequested.connect(self.showCallViewContextMenu)
        self.lib_view.clicked.connect(self.libClicked)
        self.leak_view.clicked.connect(self.leakClicked)
        self.btn_forward.clicked.connect(self.nextLeak)
        self.btn_back.clicked.connect(self.previousLeak)
        self.btn_filter_0.clicked.connect(self.updateFilter)
        self.btn_filter_1.clicked.connect(self.updateFilter)
        self.btn_filter_2.clicked.connect(self.updateFilter)
        self.btn_filter_3.clicked.connect(self.updateFilter)

    def addAsmTab(self, bin_file_path, asm_file_path):
        """Add new tab to asm tab widget.

        Args:
            bin_file_path: Path to binary without '.asm' ending
            asm_file_path: Path to binary

        Returns:
            The new tab index if successful, -1 otherwise.
        """

        try:
            with utils.datafs.get_file(asm_file_path, encoding='utf-8') as f:
                asm_dump = f.read()
        except:
            debug(1, "Asm file not found: %s", asm_file_path)
            return -1
        asm_tab_index = self.asm_tab.createNewAsmTab(bin_file_path, asm_dump)
        self.asm_tab.widget(asm_tab_index).indicatorClicked.connect(self.asmIndicatorClicked)
        self.asm_tab.setTabToolTip(asm_tab_index, bin_file_path)

        return asm_tab_index

    def addSrcTab(self, src_file_path):
        """Add new tab to src tab widget.

        Args:
            src_file_path: Path to the source file

        Returns:
            The new tab index if successful, -1 otherwise.
        """

        try:
            with utils.datafs.get_file(src_file_path, encoding='utf-8') as f:
                src_tab_index = self.src_tab.createNewSourceTab(f)
        except:
            debug(1, "Source file not found: %s", src_file_path)
            return -1
        self.src_tab.widget(src_tab_index).indicatorClicked.connect(self.srcIndicatorClicked)
        self.src_tab.setTabToolTip(src_tab_index, src_file_path)

        return src_tab_index

    def setupInfoMap(self, lib_hierarchy):
        """Setup package.utils.info_map and open asm/src tabs."""

        assert isinstance(lib_hierarchy, LibHierarchy)

        with utils.datafs.get_binfile(IP_INFO_FILE) as f:
            short_info_map = loadipinfo(f)

        for ip in sorted_keys(lib_hierarchy.entries):
            lib = lib_hierarchy.entries[ip]
            assert isinstance(lib, Library)
            lib_name = lib.libentry.name.split('/')[-1]
            lib_item = libHierarchyItem("{}".format(lib_name), lib, self.lib_model.root_item)
            self.lib_model.root_item.appendChild(lib_item)
            bin_file_path = lib.libentry.name
            asm_file_path = bin_file_path + ".asm"
            asm_tab_index = self.isFileAlreadyOpen(self.asm_tab, bin_file_path)
            if asm_tab_index == -1:
                asm_tab_index = self.addAsmTab(bin_file_path, asm_file_path)
                fl_entries = self.createLibFunctionItems(lib, lib_item)  # tuple (ip, fl_item)
                for fl_entry in fl_entries:
                    addr = fl_entry[0]
                    if addr not in short_info_map:
                        debug(0, "Cannot find addr in short_info_map")
                        debug(0, "(Could be a wrong combination of pickle and zip file?)")
                        sys.exit(ErrorCode.INVALID_COMB_OF_FILES)

                    short_info = short_info_map[addr]
                    assert isinstance(short_info, IpInfoShort)

                    if short_info.asm_line_nr >= 0:
                        # Set asm marker and indicator
                        search_str = format(utils.getLocalIp(addr), 'x') + ":"
                        if asm_tab_index != -1:
                            asm_marker_handle = self.asm_tab.widget(asm_tab_index).markerAdd(short_info.asm_line_nr,
                                                                                             utils.LeakFlags.INVESTIGATE)
                            asm_line_text = self.asm_tab.widget(asm_tab_index).text(short_info.asm_line_nr)
                            self.setAsmIndicator(addr, asm_tab_index, short_info.asm_line_nr,
                                                 asm_line_text.find(search_str), len(search_str) - 1)

                        # Set src marker and indicator
                        src_tab_index = -1
                        src_marker_handle = -1
                        src_line_nr = short_info.src_line_nr - 1  # QScintilla works zero-based
                        if short_info.src_file is not None:
                            src_tab_index = self.isFileAlreadyOpen(self.src_tab, short_info.src_file)
                            if src_tab_index == -1:
                                src_tab_index = self.addSrcTab(short_info.src_file)

                            if src_tab_index != -1:
                                src_marker_handle = self.src_tab.widget(src_tab_index).markerAdd(src_line_nr,
                                                                                                 utils.LeakFlags.INVESTIGATE)
                                src_line_text = self.src_tab.widget(src_tab_index).text(src_line_nr)
                                start_pos = len(src_line_text) - len(src_line_text.lstrip())
                                self.setSrcIndicator(addr, src_tab_index, src_line_nr, start_pos, 0)

                        else:  # file not found
                            debug(1, "Source file path missing: %s", short_info.src_file)

                        ip_info = IpInfo(asm_tab_index, short_info.asm_line_nr, asm_marker_handle, src_tab_index,
                                         src_line_nr, src_marker_handle, fl_entry[1])

                        utils.info_map[addr] = ip_info

                fl_entries.clear()

        call_item = self.call_model.root_item  # type: CallHierarchyItem
        self.findIptoCallMappings(call_item)
        self.addMissingInformation(short_info_map)

    def addMissingInformation(self, short_info_map):
        """Add missing function ip's to package.utils.info_map to enable GOTO Caller/Callee mechanism."""

        for ip in short_info_map.keys():
            if ip not in utils.info_map.keys():
                short_entry = short_info_map[ip]
                src_line_nr = short_entry.src_line_nr - 1  # QScintilla works zero-based
                bin_file_path = short_entry.asm_file.rstrip(".asm")
                asm_tab_index = self.isFileAlreadyOpen(self.asm_tab, bin_file_path)
                if asm_tab_index == -1:
                    asm_tab_index = self.addAsmTab(bin_file_path, short_entry.asm_file)
                if asm_tab_index != -1:
                    self.asm_tab.widget(asm_tab_index).markerAdd(short_entry.asm_line_nr,
                                                                 LeakFlags.RIGHT_ARROW)
                src_tab_index = -1
                if short_entry.src_file is not None:
                    src_tab_index = self.isFileAlreadyOpen(self.src_tab, short_entry.src_file)
                    if src_tab_index == -1:
                        src_tab_index = self.addSrcTab(short_entry.src_file)
                    if src_tab_index != -1:
                        self.src_tab.widget(src_tab_index).markerAdd(src_line_nr,
                                                                     LeakFlags.RIGHT_ARROW)
                ip_info = IpInfo(asm_tab_index, short_entry.asm_line_nr, -1, src_tab_index,
                                 src_line_nr, -1, None)
                utils.info_map[ip] = ip_info

    def updateFilter(self):
        self.collapseCallHierarchy()
        self.currentLeak()
        debug(1, "Update filter")

    def isFilterActive(self, leak_meta):
        assert isinstance(leak_meta, LeakMetaInfo)
        leak_flags = leak_meta.flag
        if leak_flags == LeakFlags.NOLEAK:
            return self.btn_filter_0.isChecked()
        elif leak_flags == LeakFlags.INVESTIGATE:
            return self.btn_filter_1.isChecked()
        elif leak_flags == LeakFlags.LEAK:
            return self.btn_filter_2.isChecked()
        elif leak_flags == LeakFlags.DONTCARE:
            return self.btn_filter_3.isChecked()
        else:
            debug(0, "Invalid leak flag %s", (str(leak_flags)))
            return False

    def findIptoCallMappings(self, call_item):
        """ Search call hierarchy recursively to find the correct contexts for the leaks.

        Args:
            call_item: Root item of the call hierarchy
        """
        assert isinstance(call_item, CallHierarchyItem)
        for k in sorted_keys(call_item.obj.dataleaks):
            dl = call_item.obj.dataleaks[k]
            ip = dl.ip

            if dl.meta is None:
                dl.meta = LeakMetaInfo()

            if ip in utils.info_map:
                utils.info_map[ip].call_tree_items.append(call_item)

        for k in sorted_keys(call_item.obj.cfleaks):
            cf = call_item.obj.cfleaks[k]
            ip = cf.ip

            if cf.meta is None:
                cf.meta = LeakMetaInfo()

            if ip in utils.info_map:
                utils.info_map[ip].call_tree_items.append(call_item)

        for child_item in call_item.child_items:  # type: CallHierarchyItem
            self.findIptoCallMappings(child_item)

    def setupWindowInfo(self):
        self.setWindowTitle('DATA - Differential Address Trace Analysis ' + DATAGUI_VERSION)
        window_icon = QIcon('resources/icons/window_icon.png')
        window_icon.actualSize(QSize(50, 50))
        self.setWindowIcon(window_icon)
        self.setGeometry(100, 100, 1600, 700)
        self.show()
        # self.showMaximized()

    def createLibFunctionItems(self, lib, parent_item):
        """Create tree items of library function in the lib hierarchy.

        Agrs:
            lib: The library object containing functions
            parent_item: The corresponding library tree item

        Returns:
            A tuple of (ip, fl_item), where ip is an instruction pointer
            to a leak from a function and fl_item is the tree item to
            this function.
        """
        assert isinstance(lib, Library)

        ip_fl_tuples = []
        for j in sorted_keys(lib.entries):
            fl = lib.entries[j]
            fl_item = libHierarchyItem("{}".format(getCtxName(fl.fentry)), fl, parent_item)
            parent_item.appendChild(fl_item)

            assert isinstance(fl, FunctionLeak)
            for i in sorted_keys(fl.dataleaks):
                dl = fl.dataleaks[i]
                assert isinstance(dl, DataLeak)
                ip_fl_tuples.append((dl.ip, fl_item))

            for j in sorted_keys(fl.cfleaks):
                cf = fl.cfleaks[j]
                assert isinstance(cf, CFLeak)
                ip_fl_tuples.append((cf.ip, fl_item))

        return ip_fl_tuples

    # # # # # # # # # # # # #
    # TOGGLE VIEW FUNCTIONS #
    # # # # # # # # # # # # #
    def toggleASM(self, state):
        if state:
            self.asm_tab.show()
        else:
            self.asm_tab.hide()

    def toggleSource(self, state):
        if state:
            self.src_tab.show()
        else:
            self.src_tab.hide()

    def toggleCall(self, state):
        if state:
            self.call_view.show()
            self.view_splitter.show()
            self.info_splitter.show()
        else:
            self.call_view.hide()
            self.checkViewSplitter()

    def toggleLib(self, state):
        if state:
            self.lib_view.show()
            self.view_splitter.show()
            self.info_splitter.show()
        else:
            self.lib_view.hide()
            self.checkViewSplitter()
            self.checkInfoSplitter()

    def toggleLeak(self, state):
        if state:
            self.leak_view.show()
            self.view_splitter.show()
            self.info_splitter.show()
        else:
            self.leak_view.hide()
            self.checkViewSplitter()
            self.checkInfoSplitter()

    def toggleStacked(self, state):
        if state:
            self.stacked_widget.show()
            self.info_splitter.show()
        else:
            self.stacked_widget.hide()
            self.checkInfoSplitter()

    def checkInfoSplitter(self):
        if (not self.call_view.isVisible() and not self.lib_view.isVisible() and not self.leak_view.isVisible() and
                not self.stacked_widget.isVisible()):
            self.info_splitter.hide()

    def checkViewSplitter(self):
        if not self.call_view.isVisible() and not self.lib_view.isVisible() and not self.leak_view.isVisible():
            self.view_splitter.hide()

    def isFileAlreadyOpen(self, tab_widget, file_path):
        """Check if any tab of the given widget already contains the content of file_path.

        Args:
            tab_widget: QTabTwidget object, either asm_tab or src_tab.
            file_path: Path to be checked.

        Returns:
            The tab index if the file is already present, -1 otherwise.
        """
        tab_index = -1
        for i in range(tab_widget.count()):
            if file_path == tab_widget.tabToolTip(i):
                tab_index = i
                break

        return tab_index

    def showCallViewContextMenu(self, pos):
        menu = QMenu("CallView Context Menu")

        caller_act = QAction("Go to Caller")
        caller_act.triggered.connect(self.goToCaller)
        menu.addAction(caller_act)

        callee_act = QAction("Go to Callee")
        callee_act.triggered.connect(self.goToCallee)
        menu.addAction(callee_act)

        menu.addSeparator()

        expand_act = QAction("Expand all")
        expand_act.triggered.connect(self.call_view.expandAll)
        menu.addAction(expand_act)

        collapse_act = QAction("Collapse all")
        collapse_act.triggered.connect(self.call_view.collapseAll)
        menu.addAction(collapse_act)

        menu.exec(self.call_view.viewport().mapToGlobal(pos))

    def asmIndicatorClicked(self, line_nr, line_index, pressed_key):
        map_key = utils.createKey(self.asm_tab.currentIndex(), line_nr)
        leak_ip = utils.asm_map[map_key]
        debug(5, "[ASM] Indicator clicked in line '%s', index '%s', value '%s'",
              (line_nr, line_index, str(hex(leak_ip))))
        self.coming_from_call_view = False
        ip_info = info_map[leak_ip]
        self.createLeakList(ip_info.lib_tree_item.obj)
        leak = self.selectLeakItem(leak_ip)
        if leak is not None and not isinstance(leak, QVariant):
            self.handleLeakSelection(leak)

    def srcIndicatorClicked(self, line_nr, line_index, pressed_key):
        map_key = utils.createKey(self.src_tab.currentIndex(), line_nr)
        leak_ip = utils.src_map[map_key]
        debug(5, "[SRC] Indicator clicked in line '%d', index '%d', value '%s'",
              (line_nr, line_index, str(hex(leak_ip))))
        self.coming_from_call_view = False
        ip_info = info_map[leak_ip]
        self.createLeakList(ip_info.lib_tree_item.obj)
        leak = self.selectLeakItem(leak_ip)
        if leak is not None and not isinstance(leak, QVariant):
            self.handleLeakSelection(leak)

    def setAsmIndicator(self, addr, asm_tab_index, line_nr, line_index, end_pos):
        asm_editor = self.asm_tab.widget(asm_tab_index)
        asm_editor.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
        start_pos = asm_editor.positionFromLineIndex(line_nr, line_index)
        asm_editor.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start_pos, end_pos)
        key = utils.createKey(asm_tab_index, line_nr)
        utils.asm_map[key] = addr

    def setSrcIndicator(self, addr, src_tab_index, line_nr, line_index, end_pos):
        src_editor = self.src_tab.widget(src_tab_index)
        src_editor.SendScintilla(QsciScintilla.SCI_SETINDICATORCURRENT, 0)
        start_pos = src_editor.positionFromLineIndex(line_nr, line_index)
        end_pos = src_editor.lineLength(line_nr) - line_index
        src_editor.SendScintilla(QsciScintilla.SCI_INDICATORFILLRANGE, start_pos, end_pos)
        key = utils.createKey(src_tab_index, line_nr)
        utils.src_map[key] = addr

    def callClicked(self, call_index):
        if not call_index.isValid():
            debug(1, "[CallView] Clicked: invalid index")
            return

        call_hierarchy = self.call_model.data(call_index, CustomRole.Obj)
        self.coming_from_call_view = True
        self.createLeakList(call_hierarchy)
        self.goToCallee()
        self.setColorScheme(ColorScheme.CALL)
        #self.call_view.setFocus()

    def collapseCallHierarchyRecursive(self, call_item, parent_index = None):
        """ Search call hierarchy recursively to find the correct contexts for the leaks.

        Args:
            call_item: Root item of the call hierarchy
        """
        has_active_leaks = False
        assert isinstance(call_item, CallHierarchyItem)
        for k in sorted_keys(call_item.obj.dataleaks):
            dl = call_item.obj.dataleaks[k]
            assert isinstance(dl.meta, LeakMetaInfo)
            if self.isFilterActive(dl.meta):
                has_active_leaks = True
                break
        for k in sorted_keys(call_item.obj.cfleaks):
            cf = call_item.obj.cfleaks[k]
            assert isinstance(cf.meta, LeakMetaInfo)
            if self.isFilterActive(cf.meta):
                has_active_leaks = True
                break

        index = self.findCallItemIndex(call_item.id, parent_index)

        for child_item in call_item.child_items:  # type: CallHierarchyItem
            res = self.collapseCallHierarchyRecursive(child_item, index)
            has_active_leaks = has_active_leaks or res
        if index is not None:
            if has_active_leaks:
                self.call_view.expand(index)
            else:
                self.call_view.collapse(index)

        return has_active_leaks

    def collapseCallHierarchy(self):
        # collapse call hierarchy for all hierarchy items that do not have active leaks
        # That is, their leaks are filtered
        self.collapseCallHierarchyRecursive(self.call_model.root_item)

    def setColorScheme(self, scheme):
        pal = QPalette()
        if scheme == ColorScheme.CALL:
            pal.setColor(QPalette.Text, Qt.black)
            self.call_view.setPalette(pal)
            pal.setColor(QPalette.Text, Qt.lightGray)
            self.lib_view.setPalette(pal)
            self.lib_view.selectionModel().clearSelection()
        elif scheme == ColorScheme.LIB:
            pal.setColor(QPalette.Text, Qt.lightGray)
            self.call_view.setPalette(pal)
            self.call_view.selectionModel().clearSelection()
            pal.setColor(QPalette.Text, Qt.black)
            self.lib_view.setPalette(pal)
        elif scheme == ColorScheme.BOTH:
            pal.setColor(QPalette.Text, Qt.black)
            self.call_view.setPalette(pal)
            self.lib_view.setPalette(pal)
        else:
            debug(5, "[setColorScheme] UNKNOWN context=%s", scheme)

    def createLeakList(self, obj):
        """Create all leak items for a given obj."""
        if not isinstance(obj, CallHistory) and not isinstance(obj, FunctionLeak):
            return

        if self.coming_from_call_view:
            self.leak_model.header = "Call Hierarchy Leaks"
            self.leak_model.headertooltip = "List all leaks of the selected call hierarchy element"
        else:
            self.leak_model.header = "Library Hierarchy Leaks"
            self.leak_model.headertooltip = "List all leaks of the selected library element"

        self.leak_model.clearList()
        for k in sorted_keys(obj.dataleaks):
            dl = obj.dataleaks[k]
            self.addLeakItem(obj, dl)
        for j in sorted_keys(obj.cfleaks):
            cf = obj.cfleaks[j]
            self.addLeakItem(obj, cf)

    def addLeakItem(self, obj, leak):
        """Add single leak item to leak model."""
        meta = leak.meta
        if meta is not None:
            if not self.isFilterActive(meta):
                debug(3, "Filtering data leak %x", (leak.ip))
                return

        leak_item = LeakItem(utils.leakToStr(leak), leak)
        leak_item.high_prio_flag = self.getMaxPriority(obj, leak)
        ip_info = info_map[leak.ip]
        self.updateMarginSymbol(ip_info, leak_item.high_prio_flag)
        self.leak_model.appendItem(leak_item)

    def getMaxPriority(self, obj, leak):
        """Find flag id with maximum priority.

        Args:
            obj: Either CallHistory or FunctionLeak.
            leak: leak of interest.

        Returns:
            Flag id with maximum priority, -1 if FunctionLeak
            does not have any call hierarchy items.
        """

        if isinstance(obj, CallHistory):
            return leak.meta.flag
        elif isinstance(obj, FunctionLeak):
            call_items = info_map[leak.ip].call_tree_items

            max_priority = -1
            for tree_item in call_items:
                call_hierarchy = tree_item.obj
                call_leak = None
                if isinstance(leak, DataLeak):
                    call_leak = call_hierarchy.dataleaks[leak]
                elif isinstance(leak, CFLeak):
                    call_leak = call_hierarchy.cfleaks[leak]

                if max_priority < call_leak.meta.flag:
                    max_priority = call_leak.meta.flag

            return max_priority

    def libClicked(self, lib_index):
        if not lib_index.isValid():
            debug(1, "[LibView] Clicked: invalid index")
            return

        obj = self.lib_model.data(lib_index, CustomRole.Obj)
        self.coming_from_call_view = False
        if isinstance(obj, Library):
            debug(1, "[LibView] Clicked: Lib: %s", str(obj.libentry.name.split('/')[-1]))
        elif isinstance(obj, FunctionLeak):
            debug(1, "[LibView] Clicked: FL: %s", str(obj.sym.name))
            self.createLeakList(obj)
        else:
            debug(1, "[LibView] Clicked: UNKNOWN object type")

        self.setColorScheme(ColorScheme.LIB)

    def leakClicked(self, leak_index):
        if not leak_index.isValid():
            debug(1, "[LeakView] Clicked: invalid index")
            return

        leak = self.leak_model.data(leak_index, CustomRole.Leak)
        if not isinstance(leak, QVariant):
            debug(1, "[LeakView] Clicked: %s: %s", ("DataLeak" if isinstance(leak, DataLeak) else "CFLeak",
                                                    hex(utils.getLocalIp(leak.ip))))
        if isinstance(leak, Leak):
            self.recordPrevNextEntry(leak)
            self.handleLeakSelection(leak)

    def recordPrevNextEntry(self, leak):
        leak_idx = None
        if self.coming_from_call_view:
            # Since we only record the leak IP, we in addition need to store the index
            # of our leak within ip_info.call_tree_items
            call_index = self.call_view.selectionModel().currentIndex()
            assert call_index.isValid()
            call_hierarchy = self.call_model.data(call_index, CustomRole.Obj)
            assert isinstance(call_hierarchy, CallHistory)
            ip_info = info_map[leak.ip]
            for index in range(0, len(ip_info.call_tree_items)):
                if ip_info.call_tree_items[index].obj == call_hierarchy:
                    leak_idx = index
                    break
            assert leak_idx is not None
        debug(1, "[Record] Entry: %s: %s", (self.coming_from_call_view, hex(utils.getLocalIp(leak.ip))))
        stack_info = utils.StackInfo(self.coming_from_call_view, leak.ip, leak_idx)
        utils.appendStackInfo(stack_info)
        self.updatePrevNextButtons()

    def adjustEditors(self, ip_info):
        """Switch asm/src tab and jump to editor lines containing the leak."""

        if ip_info.asm_tab_index != -1:
            self.asm_tab.setCurrentIndex(ip_info.asm_tab_index)
            self.asm_tab.jumpToLine(ip_info.asm_tab_index, ip_info.asm_line_nr)
        else:
            self.asm_tab.setCurrentIndex(self.asm_tab.empty_tab_index)

        if ip_info.src_tab_index != -1:
            self.src_tab.setCurrentIndex(ip_info.src_tab_index)
            self.src_tab.jumpToLineNumber(ip_info.src_tab_index, ip_info.src_line_nr)
        else:
            self.src_tab.setCurrentIndex(self.src_tab.empty_tab_index)

    def selectLibItem(self, lib_item_id):
        index_list = self.lib_model.match(self.lib_model.index(0, 0, QModelIndex()), CustomRole.Id,
                                          lib_item_id, 1, Qt.MatchRecursive)
        if len(index_list) > 0:
            self.lib_view.setCurrentIndex(index_list[0])

    def callListClicked(self, list_index):
        if not list_index.isValid():
            debug(1, "[callList] Clicked: invalid index")
            return

        call_item = self.call_list_model.data(list_index, CustomRole.CallItem)
        if isinstance(call_item, QVariant):
            debug(1, "[callList] Call item is empty")
            return

        call_hierarchy = self.call_list_model.data(list_index, CustomRole.Obj)
        if isinstance(call_hierarchy, QVariant):
            debug(1, "[callList] Call hierarchy is empty")
            return

        self.coming_from_call_view = True
        self.selectCallItem(call_item.id)
        self.createLeakList(call_hierarchy)
        leak = self.selectLeakItem(self.call_list_model.selected_leak.ip)
        if leak is None:
            debug(0, "[callList] Leak is empty. Try to refresh views")
        else:
            ip_info = info_map[leak.ip]
            self.selectLibItem(ip_info.lib_tree_item.id)
            self.adjustEditors(ip_info)
            self.setupInfoBox(leak)
            self.setColorScheme(ColorScheme.BOTH)
            self.recordPrevNextEntry(leak)

    def findCallItemIndex(self, call_item_id, start_index = None):
        if start_index is None:
            start_index = self.call_model.index(0, 0, QModelIndex())
        index_list = self.call_model.match(start_index, # start
                                           CustomRole.Id, # role
                                           call_item_id, # value
                                           1, # hits
                                           Qt.MatchRecursive)
        if len(index_list) > 0:
            return index_list[0]
        else:
            return None

    def selectCallItem(self, call_item_id, start_index = None):
        if start_index is None:
            start_index = self.call_model.index(0, 0, QModelIndex())
        index_list = self.call_model.match(start_index,
                                           CustomRole.Id,
                                           call_item_id, 1, Qt.MatchRecursive)
        if len(index_list) > 0:
            self.call_view.selectionModel().setCurrentIndex(index_list[0], QItemSelectionModel.ClearAndSelect)

    def selectLeakItem(self, leak_ip):
        index_list = self.leak_model.match(self.leak_model.index(0, 0, QModelIndex()), CustomRole.Ip,
                                           leak_ip, 1, Qt.MatchRecursive)
        if len(index_list) > 0:
            self.leak_view.selectionModel().setCurrentIndex(index_list[0], QItemSelectionModel.ClearAndSelect)
            return self.leak_model.data(index_list[0], CustomRole.Leak)
        else:
            return None

    def setupInfoBox(self, leak):
        if not isinstance(leak, Leak):
            debug(1, "[setupInfoBox] Leak is not a instance of Leak")
            return

        self.removeOldInfoTabs()

        # # # # #
        summary_widget = SummaryTab(leak, self.updateFlagIcon, self.notifyUnsavedChanges)
        # evidence_widget = EvidenceTab()
        # generic_widget = GenericTab()
        # specific_widget = SpecificTab()
        # # # # #
        self.info_view.addTab(summary_widget, "Summary ({})".format(str(hex(utils.getLocalIp(leak.ip)))))
        # self.info_view.addTab(evidence_widget, "Evidence")
        # self.info_view.addTab(generic_widget, "Generic")
        # self.info_view.addTab(specific_widget, "Specific")

        self.stacked_widget.setCurrentIndex(0)
        self.stacked_widget.show()

    def removeOldInfoTabs(self):
        """Remove all tabs of the info view."""

        while self.info_view.count() > 0:
            self.info_view.removeTab(0)

    def removeOldEditorTabs(self):
        """Remove all asm and src editor tabs."""

        while self.asm_tab.count() > 0:
            self.asm_tab.removeTab(0)

        while self.src_tab.count() > 0:
            self.src_tab.removeTab(0)

    def setupCallList(self, selected_leak, call_tree_items):
        item_leak_tuples = []
        for item in call_tree_items:
            assert isinstance(item, CallHierarchyItem)
            call_hierarchy = item.obj
            assert isinstance(call_hierarchy, CallHistory)
            if isinstance(selected_leak, DataLeak):
                dl = call_hierarchy.dataleaks[selected_leak]
                meta = dl.meta
                assert isinstance(meta, LeakMetaInfo)
                if not self.isFilterActive(meta):
                    debug(3, "Filtering data leak %x", (dl.ip))
                    continue
                item_leak_tuples.append((item, dl))
                pass
            elif isinstance(selected_leak, CFLeak):
                cf = call_hierarchy.cfleaks[selected_leak]
                meta = cf.meta
                assert isinstance(meta, LeakMetaInfo)
                if not self.isFilterActive(meta):
                    debug(3, "Filtering data leak %x", (cf.ip))
                    continue
                item_leak_tuples.append((item, cf))
                pass
            else:
                assert False
                return
        self.call_list_model = CallListModel(selected_leak, item_leak_tuples, self.call_model.header)
        # TODO: potential locking problem with call_list_model
        self.call_list_view.setModel(self.call_list_model)
        self.stacked_widget.setCurrentIndex(1)
        self.stacked_widget.show()

    def goToCaller(self):
        call_index = self.call_view.selectionModel().currentIndex()
        if not call_index.isValid():
            debug(1, "[goToCaller] Invalid index")
            return

        call_hierarchy = self.call_model.data(call_index, CustomRole.Obj)
        caller_ip = call_hierarchy.ctxt.caller
        if caller_ip in utils.info_map:
            ip_info = utils.info_map[caller_ip]
            self.adjustEditors(ip_info)
        else:
            debug(1, "[goToCaller] Caller ip not in info_map")
            self.src_tab.setCurrentIndex(self.src_empty_tab_index)

    def goToCallee(self):
        call_index = self.call_view.selectionModel().currentIndex()
        if not call_index.isValid():
            debug(1, "[goToCallee] Invalid index")
            return

        callee_ip = self.call_model.data(call_index, CustomRole.Obj).ctxt.callee
        if callee_ip in utils.info_map:
            ip_info = utils.info_map[callee_ip]
            self.adjustEditors(ip_info)
        else:
            debug(1, "[goToCallee] Callee ip not in info_map")
            self.src_tab.setCurrentIndex(self.src_empty_tab_index)

    def handleLeakSelection(self, leak):
        """Display views correctly after leak selection.

        Depending on self.coming_from_call_view variable we adjust the views.

        self.coming_from_call_view is True when coming from call hierarchy or call list selection.
                                   is False when coming from library hierarchy selection or editor indicators.
        """
        if leak is None:
            debug(1, "Selected leak is filtered")
            self.statusbar.showMessage('Selected leak is filtered!')
            return
        if leak.ip in utils.info_map:
            ip_info = info_map[leak.ip]  # type: IpInfo

            if self.coming_from_call_view:
                self.selectLibItem(ip_info.lib_tree_item.id)
                self.setupInfoBox(leak)
                self.adjustEditors(ip_info)
                self.setColorScheme(ColorScheme.BOTH)

            else:
                if len(ip_info.call_tree_items) == 1:
                    call_item = ip_info.call_tree_items[0]
                    call_hierarchy = call_item.obj
                    # Use leak object from CallHierarchy, which holds the correct meta data
                    call_leak = None
                    if isinstance(leak, DataLeak):
                        call_leak = call_hierarchy.dataleaks[leak]
                    elif isinstance(leak, CFLeak):
                        call_leak = call_hierarchy.cfleaks[leak]

                    self.selectCallItem(call_item.id)
                    self.selectLibItem(ip_info.lib_tree_item.id)
                    self.setupInfoBox(call_leak)
                    self.adjustEditors(ip_info)
                    self.setColorScheme(ColorScheme.BOTH)

                elif len(ip_info.call_tree_items) > 1:
                    # It might happen that the no. call_tree_items is > 1 but all are filtered.
                    self.selectLibItem(ip_info.lib_tree_item.id)
                    self.setColorScheme(ColorScheme.LIB)
                    self.setupCallList(leak, ip_info.call_tree_items)

    def restoreLeakSelection(self, stack_info):
        self.coming_from_call_view = stack_info.coming_from_call_view
        ip_info = info_map[stack_info.leak_ip]
        if not self.coming_from_call_view:
            # Sync leak view
            self.selectLibItem(ip_info.lib_tree_item.id)
            self.createLeakList(ip_info.lib_tree_item.obj)
        else:
            # Prepare call view as if we clicked there.
            # This is necessary for synchronization!
            leak_idx = stack_info.leak_idx
            self.selectCallItem(ip_info.call_tree_items[leak_idx].id)
            # Prepare Leak list
            self.createLeakList(ip_info.call_tree_items[leak_idx].obj)
        # Now select the correct leak
        leak = self.selectLeakItem(stack_info.leak_ip)
        self.handleLeakSelection(leak)

    def updateFlagIcon(self, leak_ip, flag_id):
        index_list = self.leak_model.match(self.leak_model.index(0, 0, QModelIndex()), CustomRole.Ip,
                                           leak_ip, 1, Qt.MatchRecursive)

        if len(index_list) > 0:
            self.leak_model.updateFlag(index_list[0], flag_id)

        ip_info = info_map[leak_ip]
        self.updateMarginSymbol(ip_info, flag_id)

    def notifyUnsavedChanges(self):
        self.statusbar.showMessage('Editing')
        self.unsaved_changes = True

    def notifySaved(self):
        self.statusbar.showMessage("Saved {}".format(self.pickle_path))
        self.unsaved_changes = False

    def updateMarginSymbol(self, ip_info, flag_id):
        if ip_info.asm_tab_index != -1:
            self.asm_tab.widget(ip_info.asm_tab_index).markerDeleteHandle(ip_info.asm_marker_handle)
            ip_info.asm_marker_handle = \
                self.asm_tab.widget(ip_info.asm_tab_index).markerAdd(ip_info.asm_line_nr, flag_id)

        if ip_info.src_tab_index != -1:
            self.src_tab.widget(ip_info.src_tab_index).markerDeleteHandle(ip_info.src_marker_handle)
            ip_info.src_marker_handle = \
                self.src_tab.widget(ip_info.src_tab_index).markerAdd(ip_info.src_line_nr, flag_id)

    def closeGUI(self):
        if not self.askUnsavedChanges():
            return
        QApplication.instance().quit()

    def openFiles(self):
        """Show file dialogs to open pickle and zip files."""

        pickle_file_path = self.getPickleFileFromDialog()
        if pickle_file_path is None:
            debug(0, "Please select a valid pickle file (mandatory)")
            return None

        zip_file_path = self.getZipFileFromDialog()
        if zip_file_path is None:
            debug(0, "Please select a valid zip file (mandatory)")
            return None

        # Load pickle
        self.pickle_path = pickle_file_path
        call_hierarchy = loadpickle(pickle_file_path)

        # Load zip file
        utils.resetSymbolInfo()
        utils.setupSymbolInfo(zip_file_path)
        return call_hierarchy

    def reopenFiles(self):
        if not self.askUnsavedChanges():
            return

        self.call_hierarchy = self.openFiles()
        if self.call_hierarchy is None:
            return
        lib_hierarchy = self.call_hierarchy.flatten()

        """Reset all views and show file dialogs to open pickle and zip files."""

        # Reset
        self.leak_model.clearList()
        self.removeOldEditorTabs()
        self.stacked_widget.hide()

        # Setup
        self.setupCallTree(self.call_hierarchy)
        self.setupLibTree(lib_hierarchy)
        self.setupInfoMap(lib_hierarchy)
        self.setupEmptyTabs()
        self.setupHistoryButtons()
        self.call_view.expandAll()
        self.lib_view.expandAll()

    def askUnsavedChanges(self):
        if not self.unsaved_changes:
            return True

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setText("You have unsaved changes. Do you want to save them?")
        msg.setInformativeText("If you press 'No' all unsaved changes are lost.")
        msg.setWindowTitle("Save changes")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        retval = msg.exec_()
        if retval & QMessageBox.Yes > 0:
            self.saveExistingCallHierarchy()
            return True
        elif retval & QMessageBox.No > 0:
            # Do nothing
            return True
        elif retval & QMessageBox.Cancel > 0:
            debug(1, "User aborted action due to unsaved changes")
            return False
        else:
            debug(0, "Invalid message box action: {}".format(retval))
            return False

    def askAssert(self, assert_msg, dump_path):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("An unexpected assertion happened.")
        msg.setInformativeText("The current work was stored in " + dump_path)
        msg.setDetailedText(assert_msg)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Abort | QMessageBox.Ignore)
        retval = msg.exec_()
        if retval & QMessageBox.Abort > 0:
            sys.exit(ErrorCode.ASSERT)
        elif retval & QMessageBox.Ignore > 0:
            pass

    def getPickleFileFromDialog(self):
        """Show file dialog to open pickle file and return the pickle content."""

        file_info = self.showOpenDialog("Open pickle file", "Pickle Files (*.pickle)", self.dialog_path)
        abs_file_path = file_info[0]
        if abs_file_path:
            self.dialog_path = os.path.dirname(os.path.abspath(abs_file_path))
            return abs_file_path
        else:
            debug(1, "[PICKLE_O] No file selected")
            return None

    def getZipFileFromDialog(self):
        """Show file dialog to open zip file and return the file path of the zip file."""

        file_info = self.showOpenDialog("Open framework zip file", "Zip Files (*.zip)", self.dialog_path)
        abs_file_path = file_info[0]
        if abs_file_path:
            self.dialog_path = os.path.dirname(os.path.abspath(abs_file_path))
            return abs_file_path
        else:
            debug(1, "[ZIP_O] No file Selected")
            return None

    def saveExistingCallHierarchy(self):
        """Overwrite the currently opened pickle file."""

        if self.pickle_path:
            debug(1, "[PICKLE_S] Overwrite: %s", self.pickle_path)
            storepickle(self.pickle_path, self.call_model.root_item.obj)
            self.notifySaved()
        else:
            debug(1, "[PICKLE_S] Empty pickle path")

    def saveCallHierarchy(self):
        """Save current call hierarchy into a new pickle file."""

        file_info = self.showSaveDialog("Save call hierarchy as pickle", "Pickle Files (*.pickle)", self.dialog_path)
        abs_file_path = file_info[0]
        if abs_file_path:
            debug(1, "[PICKLE_S] Save as: %s", abs_file_path)
            self.pickle_path = abs_file_path
            self.dialog_path = os.path.dirname(os.path.abspath(self.pickle_path))
            storepickle(abs_file_path, self.call_model.root_item.obj)
            self.notifySaved()
        else:
            debug(1, "[PICKLE_S] No file Selected")

    def showOpenDialog(self, window_title, file_format="All Files (*)", current_dir="."):
        file_info = QFileDialog.getOpenFileName(self, window_title, current_dir, file_format)
        return file_info

    def showSaveDialog(self, window_title, file_format="All Files (*)", current_dir="."):
        file_info = QFileDialog.getSaveFileName(self, window_title, current_dir, file_format)
        return file_info

    def increaseFontSize(self):
        """Increase font size for each asm/src editor tab by 1 pt."""

        debug(5, "Increase font size")
        self.editor_font_size += 1
        for i in range(self.asm_tab.count() - 1):
            self.asm_tab.changeFontsize(i, self.editor_font_size)
        for i in range(self.src_tab.count() - 1):
            self.src_tab.changeFontsize(i, self.editor_font_size)

    def decreaseFontSize(self):
        """Decrease font size for each asm/src editor tab by 1 pt."""

        debug(5, "Decrease font size")
        self.editor_font_size -= 1
        for i in range(self.asm_tab.count() - 1):
            self.asm_tab.changeFontsize(i, self.editor_font_size)
        for i in range(self.src_tab.count() - 1):
            self.src_tab.changeFontsize(i, self.editor_font_size)

    def updatePrevNextButtons(self):
        """Sets the enabled property of the backward and forward buttons."""

        if utils.stack_index > 0:
            self.btn_back.setEnabled(True)
        else:
            self.btn_back.setEnabled(False)

        if utils.stack_index < len(utils.leak_stack) - 1:
            self.btn_forward.setEnabled(True)
        else:
            self.btn_forward.setEnabled(False)

    def currentLeak(self):
        """Reset views to currently selected leak."""

        stack_info = utils.getCurrentStackInfo()
        if stack_info:
            self.restoreLeakSelection(stack_info)

    def previousLeak(self):
        """Reset views to previously selected leak."""

        stack_info = utils.getPrevStackInfo()
        if stack_info:
            self.restoreLeakSelection(stack_info)
        self.updatePrevNextButtons()

    def nextLeak(self):
        """Reset views to already visited leak."""

        stack_info = utils.getNextStackInfo()
        if stack_info:
            self.restoreLeakSelection(stack_info)
        self.updatePrevNextButtons()
