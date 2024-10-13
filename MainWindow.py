from PyQt5 import QtWidgets, QtGui, QtCore
from Ui_MainWindow import Ui_MainWindow
from CommitGraphWidget import CommitGraphWidget
import os
from gitexec import execute
from gitgraph import get_graph

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
        graph = CommitGraphWidget()
        ui.commits.setWidget(graph)
        ui.commits.setWidgetResizable(False)
        graph.currentChanged.connect(self.onCommitChanged)
        self.graph = graph

        def adjustSplitters():
            w = ui.centralwidget.width()
            h = ui.centralwidget.height()
            ui.verticalSplitter.setSizes([h // 3, h // 7, h // 3])
            ui.horizontalSplitter.setSizes([w // 2, w // 2])

        QtCore.QTimer.singleShot(0, adjustSplitters)


    def onPrevCommit(self):
        self.graph.selectPrev()

    def onNextCommit(self):
        self.graph.selectNext()

    def onSelect(self):
        path = QtWidgets.QFileDialog.getExistingDirectory()
        if path == "":
            return
        ui = self._ui
        ui.repo.setText(QtCore.QDir.toNativeSeparators(path))

    def _repo(self):
        ui = self._ui
        repo = ui.repo.text()
        if os.path.isdir(repo):
            return repo

    def onRepoChanged(self):
        repo = self._repo()
        if repo is None:
            return
        commits, paths = get_graph(repo)
        self.graph.init(commits, paths)

    def onCommitChanged(self, commit):
        #print('onCommitChanged', index.data())
        repo = self._repo()
        if repo is None:
            return
        
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
