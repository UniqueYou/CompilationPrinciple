import os
import pickle
import shutil
import chardet

import sys
from PyQt5 import Qt, QtGui, uic, QtWidgets
import pandas
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QInputDialog, QLineEdit, QFileDialog, \
    QAbstractItemView, QTreeWidgetItem, QApplication, QMenu, QAction, QTextEdit, QWidget
from qtpy import QtCore
from analysis_word import WordAnalysis
from inter_grammar import grammar_main as inter
from inter_grammar import my_tree as inter_tree
from QCodeEdit import QCodeEditor
import ctypes
from analysis_grammar import grammar_main as grammar
from analysis_grammar import my_tree as tree

'''
读取文件
'''


# 读取文件
def get_code(file_path: str):
    with open(file_path, 'rb') as fp:
        data = fp.read()
    encoding = chardet.detect(data)["encoding"]
    # print(f'读取文件:\t{file_path}\n编码格式:\t{chardet.detect(data)["encoding"]}')
    return data.decode(encoding=encoding)


# 保存文件
def save_code(file_path: str, code: str, encoding='utf-8'):
    with open(file_path, 'w', encoding=encoding) as fp:
        fp.write(code)


# 关于窗口
class AboutDemo(QMainWindow):
    def __init__(self):
        super(AboutDemo, self).__init__()
        self.ui = uic.loadUi("about.ui")


# 主窗口
class MainDemo(QMainWindow):

    def __init__(self):
        super(MainDemo, self).__init__()
        self.about_demo = None
        self.ui = uic.loadUi("main.ui")

        # 触发事件
        self.ui.pushButton.clicked.connect(self.print_tree)
        self.ui.actionabout.triggered.connect(self.about)
        self.ui.actionrun.triggered.connect(self.run)
        self.ui.actioninter.triggered.connect(self.inter)
        self.ui.actionsave.triggered.connect(self.save_file)
        self.ui.actionopenworkspace.triggered.connect(self.open_folder)
        self.ui.actionanalysis.triggered.connect(self.word_analysis)
        self.ui.actiongrammar_run.triggered.connect(self.grammar_analysis)
        self.ui.treeWidget.setHeaderLabels(["文件浏览"])
        self.ui.treeWidget.clicked.connect(self.item_click)
        # 文件右键菜单
        self.ui.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.treeWidget.customContextMenuRequested.connect(self.item_right_click)
        #  词法分析表格
        self.ui.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # 设置表格不可编辑
        self.ui.tableWidget.setShowGrid(False)  # 设置不显示表格线
        self.ui.tableWidget.verticalHeader().setVisible(False)  # 不显示行号
        self.ui.tableWidget_2.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget_2.setShowGrid(False)
        self.ui.tableWidget_2.verticalHeader().setVisible(False)
        self.ui.tableWidget_2.setHidden(True)
        # 代码编辑框初始化
        self.ui.edit_tabWidget.currentChanged.connect(self.tab_change)
        self.ui.edit_tabWidget.setTabsClosable(True)
        self.ui.edit_tabWidget.tabCloseRequested.connect(self.close_tab)

        self.ui.tableWidget_3.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.ui.tableWidget_3.setShowGrid(False)  # 设置不显示表格线
        self.ui.tableWidget_3.verticalHeader().setVisible(False)  # 不显示行号
        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.edit_tabWidget.setTabShape(1)
        # 变量
        self.key = pandas.read_json('Sample.json')
        self.words_analysis_token = []  # 词法分析token表
        self.words_analysis_error = []  # 词法分析错误
        self.grammar_analysis_right = []  # 语法分析正确
        self.grammar_analysis_error = []  # 语法分析错误
        self.folder_path = os.getcwd()  # 文件夹的路径
        self.tab_path = []

    def about(self):
        self.about_demo = AboutDemo()
        self.about_demo.ui.show()

    @staticmethod
    def run():
        import win32api
        win32api.ShellExecute(0, 'open', "cmd.bat", '', '', 1)  # 前台打开

    def inter(self):
        if self.ui.edit_tabWidget.currentIndex() < 0:
            QMessageBox.warning(
                self.ui,
                '警告',
                '未打开文件')
            return
        self.ui.tableWidget_3.clear()
        self.grammar_analysis()
        if self.grammar_analysis_error:
            QMessageBox.warning(
                self.ui,
                '警告',
                '语法分析有误，不能生成中间代码')
        else:
            if self.grammar_analysis_right:
                self.ui.tabWidget.setCurrentIndex(2)
                inter(self.words_analysis_token)
                inter_tree.create_inter()
                my_tree_bites = pickle.dumps(inter_tree)
                with open("tree.pkl", "wb") as f:
                    f.write(my_tree_bites)
                inter_list = inter_tree.inter.code_list
                self.ui.tableWidget_3.setRowCount(len(inter_list))
                for i in range(len(inter_list)):
                    line_no = QTableWidgetItem(str(i))
                    self.ui.tableWidget_3.setItem(i, 0, line_no)
                    if inter_list[i][0]:
                        arg1 = QTableWidgetItem(str(inter_list[i][0]))
                        self.ui.tableWidget_3.setItem(i, 1, arg1)
                    if inter_list[i][1]:
                        arg2 = QTableWidgetItem(str(inter_list[i][1]))
                        self.ui.tableWidget_3.setItem(i, 2, arg2)
                    if inter_list[i][2]:
                        arg3 = QTableWidgetItem(str(inter_list[i][2]))
                        self.ui.tableWidget_3.setItem(i, 3, arg3)
                    if inter_list[i][3]:
                        arg4 = QTableWidgetItem(str(inter_list[i][3]))
                        self.ui.tableWidget_3.setItem(i, 4, arg4)
            else:
                QMessageBox.warning(
                    self.ui,
                    '警告',
                    '请先进行语法分析')

    # item右键界面
    def item_right_click(self, position):
        item = self.ui.treeWidget.currentItem()
        item1 = self.ui.treeWidget.itemAt(position)

        if item is not None and item1 is not None:
            right_menu = QMenu()
            right_menu.addAction(QAction(u'新建文件', self))
            right_menu.addAction(QAction(u'新建目录', self))
            right_menu.addAction(QAction(u'删除', self))
            right_menu.triggered[QAction].connect(self.right_event_click)
            right_menu.exec_(QCursor.pos())

    def right_event_click(self, q):
        # 判断是项目节点还是任务节点
        command = q.text()
        print(command)
        item = self.ui.treeWidget.currentItem()
        item_path = self.get_item_path(item)
        if command == "删除":
            item.removeChild(item)
            print(item_path)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        elif command == "新建文件":
            self.new_file(item)
        elif command == '新建目录':
            self.new_dir(item)

    def new_file(self, item):
        new_file_name, ok = QInputDialog.getText(
            self,
            "新建",
            "名称:",
            QLineEdit.Normal,
            "untitled.c")
        if not ok:
            QMessageBox.warning(
                self.ui,
                '你取消了操作',
                '文件将不会被创建')
        else:
            item_path = self.get_item_path(item)  # 当前节点的路径
            if not os.path.isdir(item_path):
                item = item.parent()  # 父节点一定是文件夹
            # 新建文件标签
            self.new_table(new_file_name)
            folder_path = self.get_item_path(item)
            file_path = os.path.join(folder_path, new_file_name)
            file_path = file_path.replace('\\', '/')
            self.tab_path.append(file_path)
            # 新建文件
            save_code(file_path, '')
            # 改变文件目录
            file_info = Qt.QFileInfo(file_path)
            file_icon = Qt.QFileIconProvider()
            icon = QtGui.QIcon(file_icon.icon(file_info))
            child = QTreeWidgetItem(item)
            child.setText(0, new_file_name)
            child.setIcon(0, QtGui.QIcon(icon))

    def new_dir(self, item):
        new_dir_name, ok = QInputDialog.getText(
            self,
            "新建",
            "名称:",
            QLineEdit.Normal,
            "dir")
        if not ok:
            QMessageBox.warning(
                self.ui,
                '你取消了操作',
                '文件将不会被创建')
        else:
            item_path = self.get_item_path(item)  # 当前节点的路径
            if not os.path.isdir(item_path):
                item = item.parent()  # 父节点一定是文件夹
            dir_path = self.get_item_path(item)  # 当前节点的路径
            dir_path = os.path.join(dir_path, new_dir_name)
            dir_path = dir_path.replace('\\', '/')
            # 新建文件
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            # 改变文件目录
            file_info = Qt.QFileInfo(dir_path)
            file_icon = Qt.QFileIconProvider()
            icon = QtGui.QIcon(file_icon.icon(file_info))
            child = QTreeWidgetItem(item)
            child.setText(0, new_dir_name)
            child.setIcon(0, QtGui.QIcon(icon))

    def text_change(self):
        i = self.ui.edit_tabWidget.currentIndex()
        file_name = os.path.split(self.tab_path[i])[1]
        self.ui.edit_tabWidget.setTabText(i, file_name + '*')

    def tab_change(self):
        i = self.ui.edit_tabWidget.currentIndex()
        file_path = self.tab_path[i]
        with open(file_path, 'rb') as fp:
            data = fp.read()
            encoding = chardet.detect(data)["encoding"].upper()
        self.ui.encoding_label.setText(f'编码格式: {encoding} \n文件地址: {file_path}')

    # 获取文件点击的绝对路径
    def get_item_path(self, item):
        temp = []
        while item.parent() is not None:
            temp.append(item.text(0))
            item = item.parent()
        temp.reverse()
        real_path = self.folder_path
        for i in temp:
            real_path = os.path.join(real_path, i)
        real_path = real_path.replace('\\', '/')
        return real_path

    # 文件点击事件
    def item_click(self):
        item = self.ui.treeWidget.currentItem()
        path = self.get_item_path(item=item)

        try:
            if not os.path.isdir(path):  # 如果不是文件夹

                if path not in self.tab_path:
                    self.tab_path.append(path)
                    code = get_code(path)
                    self.new_table(path)
                    now_editor = self.ui.edit_tabWidget.currentWidget()
                    now_editor.setPlainText(code)
                    self.save_file()
                else:
                    print('文件已经打开')
                    self.ui.edit_tabWidget.setCurrentIndex(self.tab_path.index(path))
        except Exception as e:
            QMessageBox.critical(
                self.ui,
                '错误',
                '该文件类型不支持预览')
            self.tab_path.pop()

    def open_folder(self):

        path = QFileDialog.getExistingDirectory(self, "选取文件夹", "./")

        if path == '':
            QMessageBox.warning(
                self.ui,
                '警告',
                '没有文件夹被打开')
        else:
            self.folder_path = path
            self.ui.treeWidget.clear()
            self.ui.treeWidget.setColumnCount(1)
            self.ui.treeWidget.setColumnWidth(0, 50)
            self.ui.treeWidget.setHeaderLabels(["文件浏览"])
            self.ui.treeWidget.setIconSize(Qt.QSize(25, 25))
            self.ui.treeWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)

            dirs = os.listdir(path)

            file_info = Qt.QFileInfo(path)
            file_icon = Qt.QFileIconProvider()
            icon = QtGui.QIcon(file_icon.icon(file_info))
            root = QTreeWidgetItem(self.ui.treeWidget)
            root.setText(0, os.path.split(path)[1])
            root.setIcon(0, QtGui.QIcon(icon))

            self.create_tree(dirs, root, path)
            QApplication.processEvents()

    def create_tree(self, dirs, root, path):
        for i in dirs:
            path_new = os.path.join(path, i)
            if os.path.isdir(path_new):
                file_info = Qt.QFileInfo(path_new)
                file_icon = Qt.QFileIconProvider()
                icon = QtGui.QIcon(file_icon.icon(file_info))
                child = QTreeWidgetItem(root)
                child.setText(0, i)
                child.setIcon(0, QtGui.QIcon(icon))
                dirs_new = os.listdir(path_new)
                self.create_tree(dirs_new, child, path_new)
            else:
                file_info = Qt.QFileInfo(path_new)
                file_icon = Qt.QFileIconProvider()
                icon = QtGui.QIcon(file_icon.icon(file_info))
                child = QTreeWidgetItem(root)
                child.setText(0, i)
                child.setIcon(0, QtGui.QIcon(icon))

    '''
    词法分析，将结果保存到
    self.words_analysis_token
    self.words_analysis_error
    '''

    def word_analysis(self):
        if self.ui.edit_tabWidget.currentIndex() < 0:
            QMessageBox.warning(
                self.ui,
                '警告',
                '未打开文件')
            return
        now_editor = self.ui.edit_tabWidget.currentWidget()
        code = now_editor.toPlainText()
        word = WordAnalysis(code)
        right, error = word.run()
        self.words_analysis_token = right
        self.words_analysis_error = error
        self.ui.tableWidget.setRowCount(len(right))
        self.ui.tableWidget_2.setRowCount(len(error))

        for i in range(len(right)):
            line = QTableWidgetItem(str(right[i][0]))
            word = QTableWidgetItem(str(right[i][1]))
            value = QTableWidgetItem(str(right[i][2]))
            dec = QTableWidgetItem(str(right[i][3]))
            self.ui.tableWidget.setItem(i, 0, line)
            self.ui.tableWidget.setItem(i, 1, word)
            self.ui.tableWidget.setItem(i, 2, value)
            self.ui.tableWidget.setItem(i, 3, dec)
        if error:
            self.ui.tableWidget_2.setHidden(False)
            for i in range(len(error)):
                line = QTableWidgetItem(str(error[i][0]))
                word = QTableWidgetItem(error[i][1])
                self.ui.tableWidget_2.setItem(i, 0, line)
                self.ui.tableWidget_2.setItem(i, 1, word)
        else:
            self.ui.tableWidget_2.setHidden(True)
        self.ui.tabWidget.setCurrentIndex(0)

    '''
    语法分析,可以生成语法树
    '''

    def grammar_analysis(self):
        if self.ui.edit_tabWidget.currentIndex() < 0:
            QMessageBox.warning(
                self.ui,
                '警告',
                '未打开文件')
            return
        self.word_analysis()  # 先进行词法分析
        if not self.words_analysis_error:  # 词法分析没有错误
            if self.words_analysis_token:
                right, error = grammar(self.words_analysis_token)
                self.grammar_analysis_right = right
                self.grammar_analysis_error = error
                self.ui.textEdit_2.clear()
                if not error:  # 语法分析正确
                    self.ui.textEdit_2.setStyleSheet("font-size:12pt; font-weight:600;")
                    self.ui.textEdit_2.setPlainText(''.join(right))
                else:
                    self.ui.textEdit_2.setStyleSheet("font-size:14pt; font-weight:600;color:red")
                    print_temp = []
                    for line_no, error_ch, dec in error:
                        print_temp.append(f'第 {line_no} 行 {error_ch} 错误: {dec}')
                    self.ui.textEdit_2.setPlainText('\n'.join(print_temp))
                self.ui.tabWidget.setCurrentIndex(1)
            else:
                QMessageBox.warning(
                    self.ui,
                    '警告',
                    '请先进行词法分析')
        else:
            QMessageBox.warning(
                self.ui,
                '警告',
                '词法分析有误，不能进行语法分析')

    def print_tree(self):
        try:
            if self.grammar_analysis_right or self.grammar_analysis_error:
                tree.print_tree()
            else:
                QMessageBox.warning(
                    self.ui,
                    '警告',
                    '请先进行语法分析，才能产生语法树')
        except Exception:
            QMessageBox.critical(
                self.ui,
                '错误',
                '生成语法树需要安装graphviz组件'
                'https://graphviz.org/download/')

    # 保存文件
    def save_file(self):
        now_editor = self.ui.edit_tabWidget.currentWidget()
        i = self.ui.edit_tabWidget.currentIndex()
        if i >= 0:  # 如果打开了文件
            code = now_editor.toPlainText()
            save_code(file_path=self.tab_path[i], code=code)
            file_name = os.path.split(self.tab_path[i])[1]
            self.ui.edit_tabWidget.setTabText(i, file_name)

    def close_tab(self, index):
        # 获取当前处于激活状态的标签
        self.ui.edit_tabWidget.removeTab(index)
        self.tab_path.pop(index)
        print(f'成功删除标签 {index}')

    def new_table(self, file_path):
        tab_name = os.path.split(file_path)[1]
        new_tab = QCodeEditor(DISPLAY_LINE_NUMBERS=True,
                              HIGHLIGHT_CURRENT_LINE=True,
                              SyntaxHighlighter=None)
        self.ui.edit_tabWidget.addTab(new_tab, tab_name)
        self.ui.edit_tabWidget.setCurrentWidget(new_tab)
        new_tab.textChanged.connect(self.text_change)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    stats = MainDemo()
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myapp")
    stats.ui.show()
    app.exec_()
