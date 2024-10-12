from PyQt5 import QtWidgets, QtCore, QtGui
from Ui_MainWindow import Ui_MainWindow
import subprocess
import re
import os
#import tempfile
import sys

def octescape_decode(s):
    def rep(m):
        vs = [int(v, 8) for v in m.group(0).split('\\')[1:]]
        return bytes(vs).decode('utf-8')
    return re.sub('(\\\\[0-9]{3})+', rep, s)

def execute(args, cwd, split = True, octescape=True, binary=False):
    output = subprocess.check_output(args, cwd=cwd)
    if binary:
        return output
    try:
        output_text = output.decode('utf-8')
    except UnicodeDecodeError as e:
        return output
    if octescape:
        output_text = octescape_decode(output_text)
    if not split:
        return output_text
    lines = output_text.split('\n')
    return lines

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        ui = Ui_MainWindow()
        ui.setupUi(self)
        self._ui = ui
        ui.select.clicked.connect(self.onSelect)
        ui.repo.textChanged.connect(self.onRepoChanged)
        ui.save.clicked.connect(self.onSave)
        ui.prevCommit.clicked.connect(self.onPrevCommit)
        ui.nextCommit.clicked.connect(self.onNextCommit)

    def _setCommit(self, fn):
        ui = self._ui
        index = ui.commits.currentIndex()
        model = ui.commits.model()
        index = model.index(fn(index.row()), 0)
        if index.isValid():
            ui.commits.setCurrentIndex(index)

    def onPrevCommit(self):
        self._setCommit(lambda row: row - 1)

    def onNextCommit(self):
        self._setCommit(lambda row: row + 1)

    def onSelect(self):
        path = QtWidgets.QFileDialog.getExistingDirectory()
        if path == "":
            return
        ui = self._ui
        ui.repo.setText(path)

    def _repo(self):
        ui = self._ui
        repo = ui.repo.text()
        if os.path.isdir(repo):
            return repo

    def onRepoChanged(self):
        repo = self._repo()
        if repo is None:
            return
        lines = execute(['git','rev-list','--all'], cwd=repo)

        ui = self._ui

        model = QtCore.QStringListModel(lines)
        ui.commits.setModel(model)

        ui.commits.selectionModel().currentChanged.connect(self.onCommitChanged)


    def onCommitChanged(self, index):
        #print('onCommitChanged', index.data())
        repo = self._repo()
        if repo is None:
            return
        commit = index.data()
        
        lines = execute(['git','show','-s',commit], cwd=repo)
        ui = self._ui
        ui.commit.setPlainText("\n".join(lines))

        def split(line):
            cols = line.split('\t')
            if (len(cols) == 2):
                cols_ = cols[0].split(' ')
                if len(cols_) == 3:
                    hash = cols_[2]
                    name = cols[1]
                    return [hash, name]
                
        def filter_none(vs):
            return [v for v in vs if v is not None]

        lines = execute(['git','ls-tree','-r', commit], cwd=repo)
        data = filter_none([split(line) for line in lines])
        
        model = QtGui.QStandardItemModel(len(data), 2)

        for row, (hash, name) in enumerate(data):
            model.setData(model.index(row, 0), hash)
            model.setData(model.index(row, 1), name)

        ui.files.setModel(model)
        ui.files.setModelColumn(1)

        ui.files.selectionModel().currentChanged.connect(self.onCurrentFileChanged)

    def _file(self, index, binary=False):
        repo = self._repo()
        if repo is None:
            return
        ui = self._ui
        model = ui.files.model()
        hash = model.data(model.index(index.row(), 0))
        output = execute(['git','show', hash], cwd=repo, split=False, octescape=False, binary=binary)
        return output

    def onCurrentFileChanged(self, index):
        ui = self._ui
        output = self._file(index, binary=False)
        if output is None:
            return
        if isinstance(output, bytes):
            ui.file.setPlainText('binary file')
        else:
            ui.file.setPlainText(output)
        path = ui.files.currentIndex().data()
        ui.fileGroup.setTitle("File " + path)

    def onSave(self):
        ui = self._ui
        path = ui.files.currentIndex().data()
        name = os.path.basename(path)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self,None,name)
        if path == "":
            return
        output = self._file(ui.files.currentIndex(), binary=True)
        if output is None:
            return
        with open(path, "wb") as f:
            f.write(output)
        
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    mainWindow = MainWindow()
    mainWindow.show()
    args = sys.argv[1:]
    if len(args) == 1:
        path = args[0]
        mainWindow._ui.repo.setText(path)
    app.exec_()