from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QPointF, QRectF, Qt, QSizeF, QSize
from PyQt5.QtGui import QColor, QPen, QBrush, QTextOption
from Commit import Commit
from Path import Path

PAD_LEFT = 10
PAD_TOP = 10
COL_WIDTH = 18
ROW_HEIGHT = 18

class CommitGraphWidget(QtWidgets.QWidget):

    currentChanged = QtCore.pyqtSignal(str)

    def __init__(self, parent = None):
        super().__init__(parent)
        self._selected = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init([], [])
        
    def init(self, commits, paths):
        self.commits = commits
        self.paths = paths
        transform = QtGui.QTransform().translate(PAD_LEFT, PAD_TOP).scale(COL_WIDTH, ROW_HEIGHT)
        inv_transform, _ = transform.inverted()
        self._transform = transform
        self._inv_transform = inv_transform
        self.resize(self.sizeHint())

    def selected(self):
        return self._selected
    
    def currentIndex(self):
        if self._selected is None:
            return
        for i, commit in enumerate(self.commits):
            if commit.sha == self._selected:
                return i

    def selectNext(self):
        if self._selected is None:
            return
        else:
            self.selectIndex(self.currentIndex() + 1)

    def selectPrev(self):
        if self._selected is None:
            return
        else:
            self.selectIndex(self.currentIndex() - 1)

    def selectIndex(self, y):

        if y < 0 or y >= len(self.commits):
            return

        sha = self.commits[y].sha
        if sha == self._selected:
            return
        self._selected = sha
        self.currentChanged.emit(sha)
        self.update()

    def mousePressEvent(self, event):
        point = self._inv_transform.map(event.pos())
        y = point.y()
        if y < 0:
            y = 0
        if y >= len(self.commits):
            y = len(self.commits) - 1
        self.selectIndex(y)
        return super().mousePressEvent(event)
    
    def sizeHint(self):
        if len(self.commits) == 0:
            return QSize(100, 100)
        point = self._transform.map(QPointF(20, self.commits[-1].y + 1))
        return QSize(int(point.x()), int(point.y()))

    def paintEvent(self, a0):
        w = self.width() - 5 * 10
        
        painter = QtGui.QPainter(self)

        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        fm = QtGui.QFontMetricsF(self.font())
        
        commit: Commit

        commits = self.commits

        transform = self._transform

        white = QtGui.QColor(QtCore.Qt.GlobalColor.white)
        black = QtGui.QColor(QtCore.Qt.GlobalColor.black)
        red = QtGui.QColor(QtCore.Qt.GlobalColor.red)

        # draw paths:
        path: Path
        for path in self.paths:
            points = path._points
            painter.setPen(QtGui.QPen(QtGui.QColor(path._color), 2.0))
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                p1 = transform.map(QPointF(x1, y1))
                p2 = transform.map(QPointF(x2, y2))
                painter.drawLine(p1, p2)

        # draw circles
        painter.setPen(QtGui.QPen(white, 2.0))
        for commit in commits:
            painter.setBrush(QColor(commit.color))
            p = transform.map(QPointF(commit.x, commit.y))
            painter.drawEllipse(p, 5.0, 5.0)

        # draw text

        highlight = self.palette().color(QtGui.QPalette.ColorRole.Highlight)

        painter.setPen(QPen(black, 2.0))
        opt = QtGui.QTextOption(QtCore.Qt.AlignmentFlag.AlignCenter)
        for commit in commits:
            p = transform.map(QPointF(*commit.p2()) + QPointF(-0.2, -0.5))
            horizontalAdvance = fm.horizontalAdvance(commit._message)
            rect = QtCore.QRectF(p, QSizeF(horizontalAdvance + 10, ROW_HEIGHT))

            if self._selected == commit.sha:
                painter.fillRect(rect, highlight)
                painter.setPen(QPen(white, 2.0))
            else:
                painter.setPen(QPen(black, 2.0))

            painter.drawText(rect, commit._message, opt)

        # debug markers
        #markers = [(1, 22), (0, 26)]
        #markers = [(2, 31), (0, 35)]
        markers = []
        painter.setBrush(red)
        for marker in markers:
            p = transform.map(QPointF(*marker))
            painter.drawEllipse(p, 5.0, 5.0)

        super().paintEvent(a0)

