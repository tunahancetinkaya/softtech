from PyQt5.QtWidgets import QTableWidgetItem, QWidget, QTreeView, QMessageBox, QComboBox
from PyQt5.QtGui import QFont
from PyQt5 import QtCore, QtWidgets
import os
import shutil
import errno


global folder1_path
global folder2_path
folder2_path = ""
folder1_path = ""

global folder1_list
folder1_list = []
global folder2_list
folder2_list = []



class CheckableFileSystemModel(QtWidgets.QFileSystemModel):
    checkStateChanged = QtCore.pyqtSignal(str, bool)
    def __init__(self):
        super().__init__()
        self.checkStates = {}
        self.rowsInserted.connect(self.checkAdded)
        self.rowsRemoved.connect(self.checkParent)
        self.rowsAboutToBeRemoved.connect(self.checkRemoved)

    def checkState(self, index):
        return self.checkStates.get(self.filePath(index), QtCore.Qt.Unchecked)

    def setCheckState(self, index, state, emitStateChange=True):
        path = self.filePath(index)
        if self.checkStates.get(path) == state:
            return
        self.checkStates[path] = state
        if emitStateChange:
            self.checkStateChanged.emit(path, bool(state))

    def checkAdded(self, parent, first, last):
        # if a file/directory is added, ensure it follows the parent state as long
        # as the parent is already tracked; note that this happens also when
        # expanding a directory that has not been previously loaded
        if not parent.isValid():
            return
        if self.filePath(parent) in self.checkStates:
            state = self.checkState(parent)
            for row in range(first, last + 1):
                index = self.index(row, 0, parent)
                path = self.filePath(index)
                if path not in self.checkStates:
                    self.checkStates[path] = state
        self.checkParent(parent)

    def checkRemoved(self, parent, first, last):
        # remove items from the internal dictionary when a file is deleted;
        # note that this *has* to happen *before* the model actually updates,
        # that's the reason this function is connected to rowsAboutToBeRemoved
        for row in range(first, last + 1):
            # path = self.filePath(self.index(row, 0, parent))
            if path in self.checkStates:
                self.checkStates.pop(path)

    def checkParent(self, parent):

        # verify the state of the parent according to the children states
        if not parent.isValid():
            return
        childStates = [self.checkState(self.index(r, 0, parent)) for r in range(self.rowCount(parent))]
        newState = QtCore.Qt.Checked if all(childStates) else QtCore.Qt.Unchecked

        oldState = self.checkState(parent)
        if newState != oldState:
            # self.setCheckState(parent, newState)
            self.dataChanged.emit(parent, parent)

        self.checkParent(parent.parent())

    def flags(self, index):
        return super().flags(index) | QtCore.Qt.ItemIsUserCheckable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            return self.checkState(index)
        return super().data(index, role)

    def setData(self, index, value, role, checkParent=True, emitStateChange=True):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            self.setCheckState(index, value, emitStateChange)
            for row in range(self.rowCount(index)):
                # set the data for the children, but do not emit the state change,
                # and don't check the parent state (to avoid recursion)
                self.setData(index.child(row, 0), value, QtCore.Qt.CheckStateRole,
                    checkParent=False, emitStateChange=False)
            self.dataChanged.emit(index, index)
            if checkParent:
                self.checkParent(index.parent())
            return True

        return super().setData(index, value, role)




class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1024, 590)

        self.file1_button = QtWidgets.QPushButton(Form)
        self.file1_button.setGeometry(QtCore.QRect(20, 20, 150, 50))


        self.file1_text = QtWidgets.QLabel(Form)
        self.file1_text.setGeometry(QtCore.QRect(190, 20, 814, 50))

        self.file2_button = QtWidgets.QPushButton(Form)
        self.file2_button.setGeometry(QtCore.QRect(20, 90, 150, 50))

        self.file2_text = QtWidgets.QLabel(Form)
        self.file2_text.setGeometry(QtCore.QRect(190, 90, 814, 50))



        self.copybutton = QtWidgets.QPushButton(Form)
        self.copybutton.setGeometry(QtCore.QRect(522, 520, 300, 50))

        self.combo = QtWidgets.QComboBox(Form)
        self.combo.addItem("Hedef Klasörü Tut")
        self.combo.addItem("Hedef Klasörü Temizle")
        self.combo.addItem("Seçilenleri Temizle")
        self.combo.setGeometry(QtCore.QRect(202, 520, 300, 50))

        #self.file1_view = QtWidgets.QFileSystemModel(Form)
        self.file1_view = CheckableFileSystemModel()
        self.file1_view.setRootPath('')

        self.tree1 = QTreeView(Form)
        self.tree1.setGeometry(QtCore.QRect(20, 150, 482, 350))
        self.tree1.setAlternatingRowColors(True)

        #self.file2_view = QtWidgets.QFileSystemModel(Form)
        self.file2_view = CheckableFileSystemModel()
        self.file2_view.setRootPath('')
        self.tree2 = QTreeView(Form)
        self.tree2.setGeometry(QtCore.QRect(522, 150, 482, 350))
        self.tree2.setAlternatingRowColors(True)

        self.file3_view = QtWidgets.QFileSystemModel(Form)
        self.file3_view.setRootPath('')
        self.tree3 = QTreeView(Form)
        self.tree3.setGeometry(QtCore.QRect(522, 150, 482, 350))
        self.tree3.setAlternatingRowColors(True)
        self.tree3.hide()

        self.file1_view.checkStateChanged.connect(self.updateLog)
        self.file2_view.checkStateChanged.connect(self.deleteLog)


        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        self.file1_button.clicked.connect(self.file1)
        self.file2_button.clicked.connect(self.file2)

        self.copybutton.clicked.connect(self.copy_mode)

    def updatelogg(self,path):
        for j in os.listdir(path):
            if os.path.isdir(path+"/"+j):
                self.updatelogg(path+"/"+j)
            folder1_list.append(path + "/" + j)

    def deletelogg(self,path):
        for j in os.listdir(path):
            if os.path.isdir(path+"/"+j):
                self.deletelogg(path+"/"+j)
            folder1_list.remove(path + "/" + j)


    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Softtech"))
        self.file1_button.setText(_translate("Form", "Kaynak"))
        self.file2_button.setText(_translate("Form", "Hedef"))

        self.copybutton.setText(_translate("Form", "Kopyala"))
        self.file1_button.setFont(QFont('Bold', 12))
        self.file2_button.setFont(QFont('Bold', 12))

        self.copybutton.setFont(QFont('Bold', 14))

        self.combo.setFont(QFont('Bold', 14))

    def updateLog(self, path, checked):
        if checked:
            sayac = 0
            if os.path.isdir(path):

                for j in os.listdir(path):
                    if os.path.isdir(path + "/" + j):
                        self.updatelogg(path + "/" + j)
                    folder1_list.append(path + "/" + j)
                for i in folder1_list:
                    if i != path and sayac == 0:
                        sayac += 1
                        folder1_list.append(path)
            else:
                folder1_list.append(path)
        else:
            # for i in folder1_list:
            #     if i == path:
            #         folder1_list.remove(path)
            sayacc = 0
            if os.path.isdir(path):

                for j in os.listdir(path):
                    if os.path.isdir(path + "/" + j):
                        self.deletelogg(path + "/" + j)
                    folder1_list.remove(path + "/" + j)
                for i in folder1_list:
                    if i != path and sayacc == 0:
                        sayacc += 1
                        folder1_list.remove(path)
            else:
                folder1_list.remove(path)

    def deleteLog(self, path, checked):
        if checked:
            folder2_list.append(path)

        else:
            for i in folder2_list:
                if i == path:
                    folder2_list.remove(path)







    def treecopy(self,s,d):
        global folder1_path
        global folder2_path
        for items in os.listdir(s):
            ss = os.path.join(s, items)
            dd = os.path.join(d, items)
            selectt = False
            for tempp in folder1_list:
                folder_controle = s + "/" + items
                if str(tempp).replace("\\","/") == folder_controle.replace("\\","/"):
                    selectt = True
            if os.path.isdir(ss):
                self.treecopy(ss, dd)
            if selectt == True:
                        try:
                            os.makedirs(os.path.dirname(dd), exist_ok=True)
                            shutil.copy2(ss, dd)
                        except OSError as error:
                            pass


    def copy(self):
        global folder1_path
        global folder2_path

        if folder1_path != "" and folder2_path != "":
            for item in os.listdir(folder1_path):
                select = False
                s = os.path.join(folder1_path, item)
                d = os.path.join(folder2_path, item)
                for temp in folder1_list:
                    if str(temp).replace("\\","/") == s.replace("\\","/"):
                        select = True
                if os.path.isdir(s):
                    self.treecopy(s, d)

                if select == True:
                        try:
                            shutil.copy2(s, d)
                        except OSError as error:
                            pass
                else:
                    pass
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Softtech")
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("dosyalar kopyalandı")


            msgBox.exec_()
        elif folder1_path == "" and folder2_path == "":
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Softtech")
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setText("Kaynak ve Hedef klasörler belirtilmedi")
            msgBox.exec_()
        elif folder1_path == "":
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Softtech")
            msgBox.setText("Kaynak klasör belirtilmedi")
            msgBox.exec_()
        else:
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Softtech")
            msgBox.setText("Hedef klasör belirtilmedi")
            msgBox.exec_()


    def selected_delete(self,folder2_pathh):
        if folder2_pathh != "":
            if os.listdir(folder2_pathh) !=0:
                for item in os.listdir(folder2_pathh):
                    d = os.path.join(folder2_pathh, item)
                    for temp in folder2_list:
                        select = False
                        if str(temp).replace("\\","/") == d.replace("\\","/"):
                            select = True

                        if select:
                            if os.path.exists(temp):
                                if os.path.isdir(temp):
                                    shutil.rmtree(temp)
                                else:
                                    os.remove(temp)
                    if os.path.exists(d) and os.path.isdir(d):
                        self.selected_delete(d)


    def copy_mode(self):
        global folder2_path
        global folder1_path
        if self.combo.currentIndex() == 0:
            self.copy()
        elif self.combo.currentIndex() == 1:
            self.file2clear()

            self.file2_view.setRootPath(folder1_path)
            self.tree2.setModel(self.file2_view)
            self.tree2.setRootIndex(self.file2_view.index(folder1_path))
            self.tree2.hide()

            self.file3_view.setRootPath(folder2_path)
            self.tree3.setModel(self.file3_view)
            self.tree3.setRootIndex(self.file3_view.index(folder2_path))
            self.tree3.show()
            self.copy()

        else:
            self.file2_view.setRootPath(folder1_path)
            self.tree2.setModel(self.file2_view)
            self.tree2.setRootIndex(self.file2_view.index(folder1_path))
            self.tree2.hide()

            self.selected_delete(folder2_path)
            self.file3_view.setRootPath(folder2_path)
            self.tree3.setModel(self.file3_view)
            self.tree3.setRootIndex(self.file3_view.index(folder2_path))
            self.tree3.show()
            self.copy()

    def file2clear(self):
        global folder2_path
        try:
            shutil.rmtree(folder2_path)
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Softtech")
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("klasör temizlendi")
            msgBox.exec_()
            os.mkdir(folder2_path)
        except OSError as error:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Softtech")
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setText("klasör bulunamadı")
            msgBox.exec_()


    def file1(self):
        global folder1_path
        dialog = QtWidgets.QFileDialog()
        folder1_path = dialog.getExistingDirectory(None, "Select Folder")
        self.file1_text.setText(folder1_path)
        self.file1_text.setFont(QFont('Bold',12))

        self.file1_view.setRootPath(folder1_path)
        self.tree1.setModel(self.file1_view)
        self.tree1.setRootIndex(self.file1_view.index(folder1_path))



    def file2(self):
        global folder2_path
        dialog = QtWidgets.QFileDialog()
        folder2_path = dialog.getExistingDirectory(None, "Select Folder")
        self.file2_text.setText(folder2_path)
        self.file2_text.setFont(QFont('Bold', 12))
        self.file2_view.setRootPath(folder2_path)
        self.tree2.setModel(self.file2_view)
        self.tree2.setRootIndex(self.file2_view.index(folder2_path))

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(form)
    form.show()
    sys.exit(app.exec_())


main()

