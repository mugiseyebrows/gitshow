from PyQt5 import QtWidgets, QtGui, QtCore
from Ui_MainWindow import Ui_MainWindow
from CommitGraphWidget import CommitGraphWidget
import os
from gitexec import execute
from gitgraph import get_graph
import time

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        ui = Ui_MainWindow()
        ui.setupUi(self)
        self._ui = ui
        self._repo = None
        ui.openRepository.triggered.connect(self.onOpenRepository)
        ui.save.clicked.connect(self.onSave)
        ui.prevCommit.clicked.connect(self.onPrevCommit)
        ui.nextCommit.clicked.connect(self.onNextCommit)
        graph = CommitGraphWidget()
        self.graph = graph

        ui.commits.setWidget(graph)
        ui.commits.setWidgetResizable(False)
        graph.currentChanged.connect(self.onCommitChanged)
        ui.showDate.clicked.connect(self.onShowDate)
        ui.showTime.clicked.connect(self.onShowTime)
        ui.showAuthor.clicked.connect(self.onShowAuthor)

        def adjustSplitters():
            w = ui.centralwidget.width()
            h = ui.centralwidget.height()
            ui.verticalSplitter.setSizes([h // 2, h // 2])
            ui.horizontalSplitter.setSizes([w // 3, w * 2 // 3])

        QtCore.QTimer.singleShot(0, adjustSplitters)

    def onShowDate(self, value):
        self.graph.setShowDate(value)

    def onShowTime(self, value):
        self.graph.setShowTime(value)

    def onShowAuthor(self, value):
        self.graph.setShowAuthor(value)

    def onPrevCommit(self):
        self.graph.selectPrev()

    def onNextCommit(self):
        self.graph.selectNext()

    def openRepository(self, path):
        self._repo = path
        self.onRepoChanged()

    def onOpenRepository(self):
        path = QtWidgets.QFileDialog.getExistingDirectory()
        if path == "":
            return
        self.openRepository(path)

    def onRepoChanged(self):
        repo = self._repo
        if repo is None:
            return
        t1 = time.time()
        commits, paths = get_graph(repo)
        t2 = time.time()
        print("get_graph took {:.3f} s".format(t2 - t1))
        self.graph.init(commits, paths)

    def onCommitChanged(self, commit):
        #print('onCommitChanged', index.data())
        repo = self._repo
        if repo is None:
            return
        
        ui = self._ui

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
        repo = self._repo
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
