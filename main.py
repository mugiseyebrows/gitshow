from PyQt5 import QtWidgets, QtCore, QtGui

import sys
from Commit import Commit
from CommitGraphWidget import CommitGraphWidget
from Path import Path
from collections import defaultdict
from MainWindow import MainWindow
from gitgraph import get_graph

def main():
    app = QtWidgets.QApplication([])
    mainWindow = MainWindow()
    mainWindow.show()
    args = sys.argv[1:]
    if len(args) == 1:
        path = args[0]
        mainWindow._ui.repo.setText(path)
    app.exec_()

def test():
    repo = sys.argv[1]
    commits, paths = get_graph(repo)
    app = QtWidgets.QApplication([])
    tree = CommitGraphWidget()
    tree.init(commits, paths)
    scrollArea = QtWidgets.QScrollArea()
    scrollArea.setWidget(tree)
    scrollArea.show()
    app.exec_()

if __name__ == "__main__":
    main()
    #test()